import os

from natsort import natsorted

from ..models import WorkDirectory
from ..utils.constants import OUTPUT_SUFFIX, POSTPROCESS_SUFFIX, SUPPORTED_IMG_TYPES
from ..utils.errors import DirectoryException
from .global_logger import logFunc


class DirectoryExplorer:
    def run(self, input, output, **kwargs):
        main_directory = self.get_main_directory(input, output, **kwargs)
        working_directories = self.explore_directories(main_directory)
        return working_directories

    @logFunc(inclass=True)
    def get_main_directory(self, input: str, output: str, **kwargs: str) -> WorkDirectory:
        """Gets the main working directory for a given input path"""
        if not input:
            raise DirectoryException("Missing Input Directory")
        input_path = os.path.abspath(input)
        
        output_path = os.path.abspath(output) or kwargs.get('output', input_path + OUTPUT_SUFFIX)
        postprocess_path = kwargs.get('postprocess', input_path + POSTPROCESS_SUFFIX)
        return WorkDirectory(input_path, output_path, postprocess_path)

    @logFunc(inclass=True)
    def explore_directories(self, main_directory: WorkDirectory) -> list[WorkDirectory]:
        """Gets all the possible working directories from main paths"""
        processed_directories = []
        #compare directories to see if it's already been stitched
        #This is inefficient as fuck but CBA to make a better one
        for (dir_root, folders, files) in os.walk(
            main_directory.output_path, topdown=True
        ):
            img_files = False
            for file in files:
                if file.lower().endswith(SUPPORTED_IMG_TYPES):
                    img_files = True
                    break
            if img_files:
                rel_root = os.path.relpath(dir_root, main_directory.output_path)
                processed_directories.append(rel_root)
        
        work_directories = []

        for (dir_root, folders, files) in os.walk(
            main_directory.input_path, topdown=True
        ):
            img_files = []
            for file in files:
                if file.lower().endswith(SUPPORTED_IMG_TYPES):
                    img_files.append(file)
            img_files = natsorted(img_files)
            if img_files:
                rel_root = os.path.relpath(dir_root, main_directory.input_path)
                if any(x for x in processed_directories if x == rel_root):
                    continue
                dir_output = os.path.join(main_directory.output_path, rel_root)
                dir_subprocess = os.path.join(main_directory.postprocess_path, rel_root)
                directory = WorkDirectory(dir_root, dir_output, dir_subprocess)
                directory.input_files = img_files
                work_directories.append(directory)
               
        if not (work_directories):
            raise DirectoryException('No valid work directories were found!')
        return work_directories
