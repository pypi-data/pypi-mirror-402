import sys
from tqdm import tqdm
import ollama
from pathlib import Path
from shutil import copy2
import threading
from .settings import settings
from .cache_manager import CacheManager
import logging
import re
logger = logging.getLogger(__name__)


class Translator:
    def __init__(self, cache_path: Path):
        self.cache = CacheManager(cache_path)
        self.lock = threading.Lock()

    def protect_syntax(self, text: str, protect_callback: callable):
      """
      Scans text for Markdown/Docusaurus syntax and replaces it with placeholders.

      This function identifies technical and structural syntax—such as code blocks, 
      LaTeX math, Docusaurus admonitions, and JSX components—and applies a 
      protection callback to prevent them from being modified during translation. 
      It ensures that technical syntax remains valid while allowing the 
      surrounding prose to be localized.
      
      Args:
        text (str): The raw Markdown or MDX content to be processed.
        protect_callback (callable): A function or method that takes the 
            matched string and returns a placeholder string (e.g., `[PROTECTED_0]`).

      Returns:
          str: The processed text with all identified technical syntax replaced 
              by placeholders.
      """
      
      # TODO: Replace this with tree-sitter or similar to redact code blocks depends on the file extension
      # List of patterns to protect (Order matters! Larger blocks first)
      patterns = [
        r'(?s:^---[\s\S]+?---)',                                          # Frontmatter
        r'(?s:```[\s\S]*?```)',                                           # Code Blocks
        r'(?s:<CodeBlock[^>]*>[\s\S]*?</CodeBlock>)',                     # Docusaurus CodeBlock
        r'(?m:^:::[a-zA-Z]+(?:\[.*?\])?\s*$)',                            # Admonition Start
        r'(?m:^:::\s*$)',                                                 # Admonition End
        r'(?s:<[a-zA-Z][\w:.-]*(?:\s+[a-zA-Z0-9:-]+=(?:"[^"]*"|\'[^\']*\'|\{[^}]*\}|[^ >]+))*\s*/?>)', # Opening Tags (All HTML/JSX)
        r'(?m:</[a-zA-Z][\w:.-]*\s*>)',                                   # Closing Tags (All HTML/JSX)
        r'(?s:\$\$[\s\S]*?\$\$)',                                         # Display Math
        r'(?<!\$)\$[^\$\n]+\$(?!\$)',                                     # Inline Math
        r'`[^`\n]+`',                                                     # Inline Code
        r'(?<=\]\()([^\)\s]+)(?=\))',                                     # Link URLs
        r'(?m:^import\s+.*?;$)'                                           # MDX Imports
      ]
      combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
      return re.sub(combined_pattern, lambda m: protect_callback(m.group(0)), text)
  
    def translate_text(self, text: str, target_lang: str = settings.target_lang, model: str = settings.ollama_model) -> str:
        """
        Sends text to the Ollama API for translation using a specified model,
        protecting technical syntax with temporary placeholders.

        Args:
          text (str): The raw content of the file to be translated.
          target_lang (str): The language to translate the text into (e.g., 'Chinese').
          model (str): The name of the Ollama model to use for translation.

        Returns:
          str: The translated text content with original technical syntax preserved.
        """
        placeholders = {}

        def protect(text_content):
            placeholder = f"[[DOC_REF_{len(placeholders)}]]"
            placeholders[placeholder] = text_content # No need for .group(0)
            return placeholder

        protected_text = self.protect_syntax(text, protect)
        
        system_prompt = (
            f"You are an expert technical translator. Translate the document into {target_lang}.\n"
            "CRITICAL: Do not modify or translate tokens like [[DOC_REF_N]].\n"
            "Preserve all structural symbols. Output ONLY the translated text."
        )

        user_prompt = f"TEXT TO TRANSLATE:\n\n{protected_text}"

        try:
            ollama.chat(model)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                self.pull_model_with_progress(model)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                options={"temperature": settings.temperature}
            )
            translated = response['message']['content'].strip()

            for placeholder, original_value in placeholders.items():
                translated = translated.replace(placeholder, original_value)

            return translated

        except Exception as e:
            logger.error("Translation Failed.")
            logger.info(e)
            return text

    def process_file(self, file_path: Path, input_root: Path, output_root: Path):
        """
        Handles the logic for a single file: translates it if it matches allowed 
        extensions, otherwise copies it directly to the output directory.

        Args:
          file_path (Path): The path to the source file.
          input_root (Path): The root directory of the source files for relative path calculation.
          output_root (Path): The root directory where translated/copied files will be saved.
        """
        new_file_path = output_root / file_path.relative_to(input_root)

        if not self.cache.file_changed(file_path):
            return

        new_file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.suffix in settings.translate_file_types:
            content = file_path.read_text(encoding='utf-8')
            translated = self.translate_text(
                content, settings.target_lang, settings.ollama_model)
            new_file_path.write_text(translated, encoding='utf-8')
        else:
            copy2(file_path, new_file_path)

        self.cache.update(file_path)

    def pull_model_with_progress(self, model_name: str):
        """
        Downloads a model from the Ollama registry while displaying a real-time 
        progress bar using tqdm for each layer.

        Args:
          model_name (str): The name of the model to pull (e.g., 'translategemma:4b').

        Raises:
          SystemExit: Exits the program with code 1 if the download fails.
        """
        print(f"Attempting to pull model: {model_name}")
        logger.info(f"Attempting to pull model: {model_name}")
        current_digest = ''
        progress_bars = {}

        try:
            for progress in ollama.pull(model_name, stream=True):
                digest = progress.get('digest', '')

                if digest != current_digest and current_digest in progress_bars:
                    progress_bars[current_digest].close()

                if not digest:
                    print(progress.get('status'))
                    continue

                if digest not in progress_bars and (total := progress.get('total')):
                    progress_bars[digest] = tqdm(
                        total=total,
                        desc=f'Downloading {digest[7:19]}',
                        unit='B',
                        unit_scale=True
                    )

                if completed := progress.get('completed'):
                    progress_bars[digest].update(
                        completed - progress_bars[digest].n)

                current_digest = digest

            for bar in progress_bars.values():
                bar.close()
            print(f"Model {model_name} pull complete.")

        except Exception as e:
            print(f"An error occurred while pulling model: {e}")
            sys.exit(1)
