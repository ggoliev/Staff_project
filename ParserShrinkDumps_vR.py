import os
import re
import logging
import subprocess
import time

#  ROEI - I suggest to move the log handlers to different file, it can be common for other files and save this file shorter
#  ToDo: config file for logging
logger = logging.getLogger('GG_Logger')
FORMAT = '[%(asctime)s]-[%(levelname)s]-[%(funcName)s] - %(message)s'
file_logger = logging.FileHandler(r'C:\Work\log.log')  # ROEI - I suggest to use parameter (for future usages)
file_logger_format = logging.Formatter(FORMAT)
file_logger.setFormatter(file_logger_format)  # tell the handler to use the above format
logger.addHandler(file_logger)  # finally, add the handler to the base logger
logger.setLevel(logging.DEBUG)

#  now we can add the console_logger logging
console_logger = logging.StreamHandler()
console_logger_format = logging.Formatter(FORMAT)
console_logger.setFormatter(console_logger_format)
logging.getLogger('GG_Logger').addHandler(console_logger)
console_logger.setLevel(logging.DEBUG)
#  ---------------------------------------General constants-----------------------------------------------
vvtool_output_folder = r'C:\Work\Amir'
pattern_dump = r'.*\d\.dump'  # ROEI - I suggest to pre compile the RE, see:
# https://stackoverflow.com/questions/452104/is-it-worth-using-pythons-re-compile
pattern_robot_data = r'DataPos0.xml'  # ROEI - are you sure you want just this file and not all the DataPos files?
dumps_list: list = []
# --------------------------------------------Constants for parsing----------------------------------------------------
app_path = r'C:\Work\TestingWorkbench.exe'
raw_file = r'C:\Work\SFT_G5_HEAT_FW_CFG_Cambria.raw'
bitmap = '0x8C8000000400001'


#  ------------------------Search all .dumps file exclude _b.dumps -----------------------------------------------------
def dumps_listing() -> list:
    """
    Go over vvtool story output folder or all vvtool output folder. "vvtool_output_folder" constant.
    Delete all the files and empty folders exclude:
    - .dump files (not _b.dumps) -> add to dumps_list for the next parsing. "pattern_dump" constant.
    - DataPos0.xml (from "RobotData" folder) -> leave as is. May be it can be helpful with recordings.
    :return: list
    """
    logger.debug('Start adding .dump files to a list and deleting all the others')
    for subdir, dirs, files in os.walk(vvtool_output_folder, topdown=False):
        for file in files:
            if re.match(pattern_dump, file):  # ROEI - are you sure its not adding _b files?
                logger.debug(f'Added to dumps_list: {os.path.join(subdir, file)}')
                dumps_list.append(os.path.join(subdir, file))
            elif re.match(pattern_robot_data, file):
                pass
            else:
                logger.debug(f'This file will be deleted: {file}')
                os.remove(os.path.join(subdir, file))
                logger.debug(f'File was deleted.')
        try: # ROEI - instead of try\catch I suggest to add check if the folder is empty (more readable code)
            logger.debug(f'This folder will be deleted: {subdir}')
            os.rmdir(subdir)
            logger.debug('Folder was deleted.')
        except OSError:
            logger.debug(f'Can\'t delete this dir: {subdir}, may be it\'s not empty ')
    return dumps_list  # ROEI - its global, you dont need to return it. I suggest to not use globals, create empty list
    # in the method and return it. the next method will get it as argument.


def testingworkbench(dump_file: str, output_folder: str, ) -> None:
    # ROEI - I suggest to change to: runTestingworkbenchWithRecording
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

# ROEI - this method need to be called: validateFwOutput
def count_files_in_folder(dump_path) -> None:
    # ROEI - see naming convention, you can use CamelCaseName or underline_name, but not both
    """
    Check the quantity and size of all (dump and parsed) files in the folder with dump. The size of a file should be
    more than 1 kb, and the quantity of files should be
    "quantity of parsed files with the specified bitmap + 1 dump file"
    :param dump_path:
    :return: None
    """
    output_folder = os.path.dirname(dump_path)  # ToDo: the same var exists in parsing function. How can I use only 1? #Roei - dont! it better to separate
    logger.debug(f'Output folder is {output_folder}')

    with os.scandir(output_folder) as entries:
        logger.debug(f'Folder {output_folder} contains:')
        for entry in entries:
            file_size = os.path.getsize(entry) / 1024  # ROEI - why 1024? please use constant
            #  the second variant is os.stat(entry).st_size
            if file_size <= 1:
                logger.warning(f'{entry.name: >{50}}, {file_size:.3f} KB. File is not parsed.')
            else:
                logger.debug(f'{entry.name: >{50}}, {file_size:.3f} KB. ')

    # ROei - isnt it the same loop as before?
    path, dirs, files = next(os.walk(output_folder))
    number_files_in_folder = (len(files))
    if number_files_in_folder < 9:
        logger.warning('Missing files!')
    #consider doing it boolean method if the parsing failed


def parsing() -> None:  # ROEI - I suggest to change the name to: parseShrinkRecording
    """
    Substitutes values from "dumps_list" files as parameters "dump_file" (-in) and "output_folder" (-out)
    to the testingworkbench function.
    Saves the parsed xmls in the same folder that dump file is .
    :return:
    """
    for dump in dumps_list:
        logger.debug(f'\n..........Parsing dump file N{dumps_list.index(dump)} from {len(dumps_list)}..........')
        output_folder = os.path.dirname(dump)
        logger.debug(f'The output folder is {output_folder}')

        testingworkbench(dump, output_folder)
        count_files_in_folder(dump)


start_time = time.time()
dumps_listing()
parsing()
end_time = time.time()
logger.info(f'Script running time is {(end_time - start_time) // 60} minutes')
