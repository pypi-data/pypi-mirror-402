import os
import re
from pathlib import Path


class LaTeXImportMerger:
    r"""Merges LaTeX files with nested \\input and \\import commands."""

    def __init__(
        self,
        verbose: bool = False,
        encoding: str = "utf-8",
        fix_graphics_paths: bool = True,
        graphics_extensions: list[str] | None = None
    ):
        self.verbose = verbose
        self.encoding = encoding
        self.fix_graphics_paths = fix_graphics_paths

        if graphics_extensions is None:
            graphics_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".tif", ".tiff", ".bmp", ".gif"]
        self.graphics_extensions = graphics_extensions

        self.processed_files = set()
        self.main_output_dir = None

    def merge_latex_file(self, main_file_path):
        main_file_path = Path(main_file_path).resolve()

        if not main_file_path.exists():
            raise FileNotFoundError(f"Main file not found: {main_file_path}")

        # Generate output filename.
        output_dir = main_file_path.parent
        output_name = main_file_path.stem + "_merged" + main_file_path.suffix
        output_file_path = output_dir / output_name

        # Store main output directory for graphics path fixing.
        self.main_output_dir = output_dir

        if self.verbose:
            print(f"Processing main file: {main_file_path}")

        # Clear processed files tracking for new merge operation.
        self.processed_files.clear()

        # Process the main file starting from its parent directory as base.
        merged_content = self._process_file(main_file_path, main_file_path.parent)

        # Write the merged content to output file.
        with open(output_file_path, "w", encoding=self.encoding) as f:
            f.write(merged_content)

        if self.verbose:
            print(f"\nMerge completed! Processed {len(self.processed_files)} files")
            print(f"Output file: {output_file_path}")

        return str(output_file_path)

    def _process_file(self, file_path, current_base_dir):
        r"""Processes a single LaTeX file.

        Reads the file, identifies \\input, \\import, and \\include commands,
        and recursively replaces them with file contents. Also fixes relative
        paths in \\includegraphics commands based on the file's context.

        Args:
            file_path: Absolute path to the file to process.
            current_base_dir: Base directory for resolving relative paths in this
                file context.

        Returns:
            str: Processed file content with imports replaced and graphics paths fixed.

        Note:
            - Adds warning comments for circular dependencies.
            - Preserves original file structure in comments.
            - Maintains proper directory context for nested imports.
            - Fixes graphics paths relative to the merged output location.
        """
        file_path_str = str(file_path.resolve())

        # Check for circular dependencies.
        if file_path_str in self.processed_files:
            print(f"⚠️  Warning: File {file_path} already processed, skipping")
            return f"% Warning: File {file_path} already included, skipping\n"

        self.processed_files.add(file_path_str)

        if self.verbose:
            print(f"  Processing: {file_path} (base directory: {current_base_dir})")

        # Read file content.
        with open(file_path, encoding=self.encoding) as f:
            content = f.read()

        # Process all import commands in sequence.
        processed_content = content

        # First, fix graphics paths if enabled.
        if self.fix_graphics_paths:
            processed_content = self._fix_graphics_paths(processed_content, current_base_dir, file_path)

        # Then process import commands.
        processed_content = self._replace_input_commands(processed_content, current_base_dir)
        processed_content = self._replace_import_commands(processed_content, current_base_dir)
        processed_content = self._replace_include_commands(processed_content, current_base_dir)

        return processed_content

    def _fix_graphics_paths(self, content, current_base_dir, source_file_path):
        r"""Fixes relative paths in \\includegraphics commands.

        Args:
            content: LaTeX content containing \\includegraphics commands.
            current_base_dir: Base directory from which relative paths should be resolved.
            source_file_path: Path to the source file (for error reporting).

        Returns:
            str: Content with fixed graphics paths.

        Note:
            - Converts relative graphics paths to be relative to the main output directory.
            - Supports optional arguments: \\includegraphics[options]{path}.
            - Handles paths with and without extensions.
            - Can copy graphics files to a common directory if copy_graphics is True.
        """
        # Regex pattern for \\includegraphics with optional arguments.
        # Matches: \includegraphics[width=0.5\textwidth]{path/to/image}
        graphics_pattern = r"\\includegraphics\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}"

        def fix_graphics_path(match):
            r"""Callback function to fix a single \\includegraphics path.

            Args:
                match: Regex match object.

            Returns:
                str: Fixed \\includegraphics command.
            """
            options = match.group(1) or ""  # Optional arguments like [width=0.5\textwidth]
            graphics_path = match.group(2).strip().strip('"').strip("'")

            # Skip if path is already absolute or uses graphicspath.
            if graphics_path.startswith("/") or graphics_path.startswith("\\") or "\\graphicspath" in content:
                return match.group(0)  # Return unchanged.

            # Find the actual graphics file.
            graphics_file = self._find_graphics_file(graphics_path, current_base_dir)

            if graphics_file is None:
                warning = f"% Warning: Graphics file not found: {graphics_path}"
                print(f"⚠️  {warning}")

                # Try common extensions.
                for ext in self.graphics_extensions:
                    test_path = current_base_dir / (graphics_path + ext)
                    if test_path.exists():
                        graphics_file = test_path
                        print(f"   Found with extension {ext}: {graphics_file}")
                        break

                if graphics_file is None:
                    return f"{match.group(0)}  % {warning}"

            # If not copying, calculate the correct relative path.
            if graphics_file and self.main_output_dir:
                # Calculate path relative to the main output directory.
                try:
                    # Make graphics path relative to main output directory.
                    rel_path = self._calculate_relative_path(graphics_file, self.main_output_dir)

                    # Check if the relative path exists.
                    test_path = self.main_output_dir / rel_path
                    if not test_path.exists():
                        # Try to find it with extensions.
                        found = False
                        for ext in self.graphics_extensions:
                            test_path = self.main_output_dir / (str(rel_path) + ext)
                            if test_path.exists():
                                rel_path = Path(str(rel_path) + ext)
                                found = True
                                break

                        if not found:
                            # File doesn't exist at that location, warn user.
                            print(f"⚠️  Graphics file not at expected location: {rel_path}")
                            # Fall back to original path with comment.
                            if options:
                                return (
                                    f"\\includegraphics[{options}]{{{graphics_path}}}  "
                                    f"% Original: {graphics_path}, Needs manual fix"
                                )
                            else:
                                return (
                                    f"\\includegraphics{{{graphics_path}}}  "
                                    f"% Original: {graphics_path}, Needs manual fix"
                                )

                    if options:
                        return f"\\includegraphics[{options}]{{{rel_path}}}"
                    else:
                        return f"\\includegraphics{{{rel_path}}}"

                except ValueError as e:
                    print(f"❌ Error calculating relative path for {graphics_file}: {e}")
                    # Fall back to original path with comment.
                    if options:
                        return (
                            f"\\includegraphics[{options}]{{{graphics_path}}}  % Original: {graphics_path}, Error: {e}"
                        )
                    else:
                        return f"\\includegraphics{{{graphics_path}}}  % Original: {graphics_path}, Error: {e}"

            # Fallback: return original command with comment.
            if options:
                return (
                    f"\\includegraphics[{options}]{{{graphics_path}}}  "
                    f"% Original: {graphics_path}, Base: {current_base_dir}"
                )
            else:
                return f"\\includegraphics{{{graphics_path}}}  % Original: {graphics_path}, Base: {current_base_dir}"

        return re.sub(graphics_pattern, fix_graphics_path, content)

    def _calculate_relative_path(self, graphics_file, target_dir):
        """Calculates relative path from target directory to graphics file.

        Args:
            graphics_file: Absolute path to the graphics file.
            target_dir: Directory from which the relative path should be calculated.

        Returns:
            Path: Relative path from target_dir to graphics_file.

        Raises:
            ValueError: If relative path cannot be calculated.
        """
        try:
            # Calculate relative path.
            rel_path = os.path.relpath(graphics_file, target_dir)
            return Path(rel_path)
        except ValueError as e:
            # On Windows, if paths are on different drives.
            print(f"⚠️  Cannot calculate relative path between {graphics_file} and {target_dir}: {e}")

            # Alternative: try to find a path that makes sense.
            # Check if graphics file is in a subdirectory of main output dir.
            try:
                # Try using path relative to graphics file's parent.
                graphics_parent = graphics_file.parent
                rel_to_parent = os.path.relpath(graphics_file, graphics_parent)

                # Try to find a reasonable relative path.
                # Check common directories like 'figures', 'images', etc.
                common_dirs = ["figures", "figs", "images", "img", "graphics"]
                for common_dir in common_dirs:
                    test_dir = target_dir / common_dir
                    if test_dir.exists():
                        # Try to construct path relative to common directory.
                        try:
                            rel_to_common = os.path.relpath(graphics_file, test_dir)
                            if not rel_to_common.startswith(".."):
                                return Path(common_dir) / rel_to_common
                        except ValueError:
                            continue

                # Last resort: return path relative to graphics parent.
                return Path(rel_to_parent)

            except Exception as e2:
                raise ValueError(f"Cannot find suitable relative path: {e2}")

    def _find_graphics_file(self, graphics_path, search_dir):
        """Locates a graphics file with various extensions in the specified directory."""
        # Check if path contains directory traversal.
        if ".." in graphics_path or graphics_path.startswith("."):
            # Resolve relative to search_dir.
            potential_path = (search_dir / graphics_path).resolve()
            if potential_path.exists():
                return potential_path

        # Try the exact path first.
        test_path = search_dir / graphics_path
        if test_path.exists():
            return test_path.resolve()

        # Try with various extensions.
        for ext in self.graphics_extensions:
            # Try graphics_path + extension.
            test_path = search_dir / (graphics_path + ext)
            if test_path.exists():
                return test_path.resolve()

            # Try graphics_path with extension replaced.
            if "." in graphics_path:
                name_without_ext = graphics_path.rsplit(".", 1)[0]
                test_path = search_dir / (name_without_ext + ext)
                if test_path.exists():
                    return test_path.resolve()

        # If still not found, try looking in subdirectories.
        # Common graphics directories.
        common_graphics_dirs = ["figures", "figs", "fig", "images", "imgs", "img", "graphics"]
        for graphics_dir in common_graphics_dirs:
            test_dir = search_dir / graphics_dir
            if test_dir.exists():
                # Try exact path in subdirectory.
                test_path = test_dir / graphics_path
                if test_path.exists():
                    return test_path.resolve()

                # Try with extensions in subdirectory.
                for ext in self.graphics_extensions:
                    test_path = test_dir / (graphics_path + ext)
                    if test_path.exists():
                        return test_path.resolve()

        return None

    def _replace_input_commands(self, content, base_dir):
        r"""Replaces \\input{} commands with file contents, skipping commented-out commands."""
        # Split content into lines for line-by-line processing
        lines = content.split('\n')
        result_lines = []

        for line in lines:
            # Skip fully commented lines
            stripped_line = line.lstrip()
            if stripped_line.startswith('%'):
                result_lines.append(line)
                continue

            # Process line, handling inline comments
            processed_line = self._process_input_line(line, base_dir)
            result_lines.append(processed_line)

        return '\n'.join(result_lines)

    def _process_input_line(self, line, base_dir):
        r"""Process a single line for \\input commands, handling inline comments."""
        # Find comment position if any
        comment_pos = line.find('%')

        if comment_pos == -1:
            # No comment in line, process entire line
            return self._replace_input_in_string(line, base_dir)
        else:
            # Has comment, split line
            code_part = line[:comment_pos]
            comment_part = line[comment_pos:]

            # Check if there's a \input command before the comment
            if '\\input' in code_part:
                # Process the code part
                processed_code = self._replace_input_in_string(code_part, base_dir)
                return processed_code + comment_part
            else:
                # No \input before comment, return line unchanged
                return line

    def _replace_input_in_string(self, text, base_dir):
        r"""Replace \\input commands in a string (assumes no comments in the string)."""
        input_pattern = r'\\input\s*(?:\{([^}]+)\}|([^\s\{]+))'

        def replace_input(match):
            r"""Callback function to replace a single \\input command.

            Args:
                match: Regex match object.

            Returns:
                str: Replacement content.
            """
            # Extract filename from either group 1 (braced) or group 2 (unbraced).
            filename = (match.group(1) or match.group(2)).strip().strip('"').strip("'")

            # Find the referenced file.
            file_path = self._find_file(filename, base_dir)

            if file_path is None:
                error_msg = f"\n% Error: Input file not found: {filename}\n"
                print(f"❌ {error_msg.strip()}")
                return error_msg

            # For \\input, nested files use the same base directory.
            replacement = f"\n% ====== Start input: {filename} ======\n"
            replacement += self._process_file(file_path, base_dir)
            replacement += f"\n% ====== End input: {filename} ======\n"

            return replacement

        return re.sub(input_pattern, replace_input, text)

    def _replace_import_commands(self, content, base_dir):
        r"""Replaces \\import{path}{file} commands with file contents, skipping commented-out commands."""
        # Split content into lines for line-by-line processing
        lines = content.split('\n')
        result_lines = []

        for line in lines:
            # Skip fully commented lines
            stripped_line = line.lstrip()
            if stripped_line.startswith('%'):
                result_lines.append(line)
                continue

            # Process line, handling inline comments
            processed_line = self._process_import_line(line, base_dir)
            result_lines.append(processed_line)

        return '\n'.join(result_lines)

    def _process_import_line(self, line, base_dir):
        r"""Process a single line for \\import commands, handling inline comments."""
        # Find comment position if any
        comment_pos = line.find('%')

        if comment_pos == -1:
            # No comment in line, process entire line
            return self._replace_import_in_string(line, base_dir)
        else:
            # Has comment, split line
            code_part = line[:comment_pos]
            comment_part = line[comment_pos:]

            # Check if there's a \import command before the comment
            if '\\import' in code_part:
                # Process the code part
                processed_code = self._replace_import_in_string(code_part, base_dir)
                return processed_code + comment_part
            else:
                # No \import before comment, return line unchanged
                return line

    def _replace_import_in_string(self, text, base_dir):
        r"""Replace \\import commands in a string (assumes no comments in the string)."""
        import_pattern = r"\\import\s*\{([^}]+)\}\s*\{([^}]+)\}"

        def replace_import(match):
            r"""Callback function to replace a single \\import command.

            Args:
                match: Regex match object.

            Returns:
                str: Replacement content.
            """
            import_path = match.group(1).strip().strip('"').strip("'")
            filename = match.group(2).strip().strip('"').strip("'")

            # Construct the import directory path.
            import_dir = Path(base_dir) / import_path

            # Find the referenced file in the import directory.
            file_path = self._find_file(filename, import_dir)

            import_filename = str(Path(import_path) / filename)
            if file_path is None:
                error_msg = f"\n% Error: Import file not found: {import_filename}\n"
                print(f"❌ {error_msg.strip()}")
                return error_msg

            # For \\import, nested files use the import directory as base.
            replacement = f"\n% ====== Start import: {import_filename} ======\n"
            replacement += self._process_file(file_path, import_dir)
            replacement += f"\n% ====== End import: {import_filename} ======\n"

            return replacement

        return re.sub(import_pattern, replace_import, text)

    def _replace_include_commands(self, content, base_dir):
        r"""Replaces \\include{} and \\includeonly{} commands with file contents.

        Note: This method also needs to skip commented-out commands. For consistency,
        we use the same line-by-line approach as _replace_input_commands.
        """
        # Split content into lines for line-by-line processing
        lines = content.split('\n')
        result_lines = []

        for line in lines:
            # Skip fully commented lines
            stripped_line = line.lstrip()
            if stripped_line.startswith('%'):
                result_lines.append(line)
                continue

            # Process line, handling inline comments
            processed_line = self._process_include_line(line, base_dir)
            result_lines.append(processed_line)

        return '\n'.join(result_lines)

    def _process_include_line(self, line, base_dir):
        r"""Process a single line for \\include commands, handling inline comments."""
        # Find comment position if any
        comment_pos = line.find('%')

        if comment_pos == -1:
            # No comment in line, process entire line
            return self._replace_include_in_string(line, base_dir)
        else:
            # Has comment, split line
            code_part = line[:comment_pos]
            comment_part = line[comment_pos:]

            # Check if there's a \include command before the comment
            if '\\include' in code_part:
                # Process the code part
                processed_code = self._replace_include_in_string(code_part, base_dir)
                return processed_code + comment_part
            else:
                # No \include before comment, return line unchanged
                return line

    def _replace_include_in_string(self, text, base_dir):
        r"""Replace \\include commands in a string (assumes no comments in the string)."""
        include_pattern = r"\\include(?:only)?\s*\{([^}]+)\}"

        def replace_include(match):
            r"""Callback function to replace a single \\include command.

            Args:
                match: Regex match object.

            Returns:
                str: Replacement content.
            """
            filename = match.group(1).strip().strip('"').strip("'")

            # Find the referenced file.
            file_path = self._find_file(filename, base_dir)

            if file_path is None:
                error_msg = f"\n% Error: Include file not found: {filename}\n"
                print(f"❌ {error_msg.strip()}")
                return error_msg

            # \\include maintains the same base directory like \\input.
            replacement = f"\n% ====== Start include: {filename} ======\n"
            replacement += self._process_file(file_path, base_dir)
            replacement += f"\n% ====== End include: {filename} ======\n"

            return replacement

        return re.sub(include_pattern, replace_include, text)

    def _find_file(self, filename, search_dir):
        """Locates a file with various extensions in the specified directory."""
        # Check if filename is an absolute path.
        if Path(filename).is_absolute():
            if Path(filename).exists():
                return Path(filename).resolve()

        # Common LaTeX file extensions to try.
        extensions = [".tex", ""]

        for ext in extensions:
            # Try filename with extension appended.
            test_path = search_dir / (filename + ext)
            if test_path.exists():
                return test_path.resolve()

            # Try filename as-is (may already have extension).
            test_path = search_dir / filename
            if test_path.exists():
                return test_path.resolve()

        return None

    def find_all_imports(self, main_file_path):
        """Discovers all files referenced by import commands without merging."""
        main_file_path = Path(main_file_path).resolve()

        files_info = []  # List of (file_path, base_dir, import_method).

        def _find_in_file(file_path, base_dir, processed):
            """Recursive helper function to find imports in a file.

            Args:
                file_path: File to analyze.
                base_dir: Base directory for this file's context.
                processed: Set of processed (file_path, base_dir) pairs to avoid cycles.
            """
            # Create unique key for this file in its directory context.
            file_key = (str(file_path.resolve()), str(base_dir))
            if file_key in processed:
                return

            processed.add(file_key)
            files_info.append((file_path, base_dir, "direct"))

            try:
                with open(file_path, encoding=self.encoding) as f:
                    content = f.read()
            except Exception as e:
                print(e)
                return

            # Find all \\input commands.
            input_pattern = r"\\input\s*(?:\{([^}]+)\}|([^\s\{]+))"
            for match in re.finditer(input_pattern, content):
                filename = (match.group(1) or match.group(2)).strip().strip('"').strip("'")
                found = self._find_file(filename, base_dir)
                if found:
                    _find_in_file(found, base_dir, processed)

            # Find all \\import commands.
            import_pattern = r"\\import\s*\{([^}]+)\}\s*\{([^}]+)\}"
            for match in re.finditer(import_pattern, content):
                import_path = match.group(1).strip().strip('"').strip("'")
                filename = match.group(2).strip().strip('"').strip("'")
                import_dir = Path(base_dir) / import_path
                found = self._find_file(filename, import_dir)
                if found:
                    _find_in_file(found, import_dir, processed)

        # Start recursive discovery from main file.
        _find_in_file(main_file_path, main_file_path.parent, set())

        # Display results.
        if self.verbose:
            print(f"Found {len(files_info)} related files:")
            for i, (file_path, base_dir, import_type) in enumerate(files_info, 1):
                rel_path = os.path.relpath(file_path, main_file_path.parent)
                print(f"  {i:3d}. {rel_path}")
                print(f"       Base directory: {os.path.relpath(base_dir, main_file_path.parent)}")
                print(f"       Import method: {import_type}")

        return files_info
