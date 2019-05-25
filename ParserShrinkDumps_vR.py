import os
import re
import subprocess
import time
import logging.config

logging.config.fileConfig(fname=r'C:\Work\logging.config', disable_existing_loggers=False)
logger = logging.getLogger('sampleLogger')
# ToDo: turtle

#  ---------------------------------------General constants-----------------------------------------------
work_folder = r'C:\Work\Line_P1_D1_1_0'
pattern_dump = re.compile(r'.*\d\.dump')
pattern_robot_data = re.compile(r'DataPos0.xml')
# --------------------------------------------Constants for parsing----------------------------------------------------
app_path = r'C:\Work\TestingWorkbench.exe'
raw_file = r'C:\Work\SFT_G5_HEAT_FW_CFG_Cambria.raw'
bitmap = '0x8C8000000400001'


def dumps_listing(vvtool_output_folder: str) -> list:
    """Create list of .dumps files in the output folder.

    Go over vvtool story output folder or all vvtool output folder. "vvtool_output_folder" constant.
    Delete all the files exclude:
    - .dump files (not _b.dumps) -> add to dumps_list for the next parsing. "pattern_dump" constant.
    - DataPos0.xml (from "RobotData" folder) -> leave as is. May be it can be helpful with recordings.
    Delete all empty (that listdir is not True (==0) folders.
    :return: list
    """
    logger.debug(f'Start adding .dump files from {vvtool_output_folder} to a list and deleting all the others.')
    global dumps_list
    dumps_list = []
    for subdir, dirs, files in os.walk(vvtool_output_folder, topdown=False):
        for file in files:
            if pattern_dump.match(file):
                logger.debug(f'File {file} match the {pattern_dump} pattern. '
                             f'Added to dumps_list: {os.path.join(subdir, file)}')
                dumps_list.append(os.path.join(subdir, file))
            elif pattern_robot_data.match(file):
                logger.debug(f'File {file} match the {pattern_robot_data}. Pass.')
            else:
                logger.debug(f'File will be deleted: {file}')
                os.remove(os.path.join(subdir, file))
                logger.debug(f'Deleted file: {file}')
        if not os.listdir(subdir):
            logger.debug(f'Folder will be deleted: {subdir}')
            os.rmdir(subdir)
            logger.debug(f'Deleted folder: {subdir}')
        else:
            logger.debug(f'Folder: {subdir} is not empty. Will not be deleted.')
    return dumps_list


def run_testingworkbench(dump_file: str, output_folder: str, ) -> None:
    """
    Run the the the testingworkbench application with needed parameters.
    Config (raw file) and extended (bitmap) parameters are predefined
    :param dump_file: str
    :param output_folder: str
    :return: None
    """
    logger.info(f'Will run {app_path} \n'
                f'-config {raw_file} \n'
                f'-in {dump_file} \n'
                f'-out {output_folder} \n'
                f'-extended {bitmap}')
    subprocess.call([app_path,
                     '-config', raw_file,
                     '-in', dump_file,
                     '-out', output_folder,
                     '-extended', bitmap])
    logger.info(f'### File is parsed ###')


def count_files_in_folder(dump_path: str) -> None:  # ROEI - this method need to be called: validateFwOutput
    """Check the quantity and size of all (dump and parsed) files in the folder with .dump file.

    The size of a file should be more than 1 kb, and the quantity of files should be
    "quantity of parsed files with the specified bitmap + 1 dump file"
    :param dump_path: path to folder with .dump file and parsed .csv files
    :return: None
    """
    logger.debug(f'Start function with parameter {dump_path}')
    output_folder = os.path.dirname(dump_path)
    logger.debug(f'Output folder is {output_folder}')

    with os.scandir(output_folder) as entries:
        logger.debug(f'Folder {output_folder} contains:')
        for entry in entries:
            file_size = os.path.getsize(entry) / 1024  # ROEI - why 1024? please use constant
            if file_size <= 1:
                logger.warning(f'{entry.name: >{50}}, {file_size:.3f} KB. File is not parsed.')
            else:
                logger.debug(f'{entry.name: >{50}}, {file_size:.3f} KB. ')

    # ROei - isn't it the same loop as before?
    path, dirs, files = next(os.walk(output_folder))
    number_files_in_folder = (len(files))
    if number_files_in_folder < 9:
        logger.warning('Missing files!')
    # Roie  consider doing it boolean method if the parsing failed


def parse_shrink_recording() -> None:
    """Run the testingworkbench app for files from dumps_list.

    Substitutes files from result of dumps_listing function as parameters "dump_file" (-in) and "output_folder" (-out)
    to the runTestingworkbenchWithRecording function.
    Output folder - is the same folder where the .dump file is, so all files will be in the one folder.
    After parsing files size and quantity are checked (count_files_in_folder function)
    :return:
    """
    for dump in dumps_list:
        logger.debug(f'\n..........Parsing dump file N{dumps_list.index(dump)} from {len(dumps_list)}..........')
        output_folder = os.path.dirname(dump)
        logger.debug(f'Parsed files will be saved in {output_folder} folder.')
        run_testingworkbench(dump, output_folder)
        count_files_in_folder(dump)


start_time = time.time()
dumps_listing(work_folder)
parse_shrink_recording()
end_time = time.time()
logger.info(f'Script running time is {(end_time - start_time) // 60} minutes')
