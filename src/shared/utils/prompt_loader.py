from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class PromptLoader:
    """
    This class supports:
    - Default directory loading
    - Custom absolute path loading
    - Relative path loading
    """

    prompts_dir: Path

    # Create loader using directory of this file
    @classmethod
    def from_module_dir(cls) -> "PromptLoader":
        """
        Initialize loader using the shared prompts directory.
        """
        # __file__ is src/shared/utils/prompt_loader.py
        # prompts are in src/shared/prompts/
        current_dir = Path(__file__).resolve().parent
        prompts_dir = current_dir.parent / "prompts"
        return cls(prompts_dir=prompts_dir)

    # Main loader method

    def load_prompt_text(
        self,
        path: Union[str, Path],
        *,
        absolute_path: bool = False, # An absolute path: Starts from the root of the file system Does NOT depend on the current working directory
        encoding: str = "utf-8",
    ) -> str:
        """
        Load prompt text.
        Args:
            path:
                - If absolute_path=False → treated as inside prompts_dir # A relative path depends on where your program is running
                - If absolute_path=True → treated as full system path
            absolute_path:
                Whether to treat `path` as absolute path 
            encoding:
                File encoding

        Returns:
            Prompt content (str)
        """

        path = Path(path)

        # If absolute path explicitly requested
        if absolute_path:
            final_path = path
        else:
            # If path is already absolute, respect it
            if path.is_absolute():     
                final_path = path
            else:
                # Otherwise load from prompts_dir
                final_path = self.prompts_dir / path

        if not final_path.exists():
            print(final_path)
            raise FileNotFoundError(f"Prompt file not found: {final_path}")

        # Explicit file handling
        with final_path.open("r", encoding=encoding) as f:
            content = f.read()

        #print('content')
        #print(content)
        return content