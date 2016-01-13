import os
import fake_filesystem_unittest


class FakeFSTestCase(fake_filesystem_unittest.TestCase):
    """Base class for test cases relies on file system structure"""

    def _create_file_structure(self, file_structure):
        """Create file structure described in dict

        Dictionary keys are paths, values are file/dictionary contents.
        If value is string, file is created with value as file contents.
        If value is dict, dictionary id created. To dict describing directory
        applies the same rules as to dict describing file structure.

        :param file_structure: dict describing file structure
        :type file_structure: dict
        :raises: :exc:`ValueError` if dict describing file structure is invalid
        """

        for file_path, contents in file_structure.items():
            if isinstance(contents, str):
                self.fs.CreateFile(file_path, contents=contents)
            elif isinstance(contents, dict):
                os.makedirs(file_path)
                self._create_file_structure(contents)
            else:
                raise ValueError('File structure value must be string or dict')
