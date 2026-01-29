import sys
import os
import logging
import paramiko
import socks # pysocks needs to be installed
import stat
import re
import xml.etree.ElementTree as ET
import pandas as pd
import io

from pathlib import Path
from time import sleep


# class to download or upload files from/to Kiteworks
class Kiteworks_io():

   # private constants
   __ERROR_OCCURRED = "An error occurred: "
   __OUTCOME_SUCCESS = "Outcome: Success"
   __DOWNLOAD_SUCCESS = "Successful download of this file: "
   __NO_FILE_TO_DOWNLOAD = "No file to be downloaded from: "
   __NO_SFTP_CLIENT = "No SFTP Client, check Kiteworks sftp access key"

   
   # Initialise Kiteworks_io
   def __init__(self, 
                sftp_access_key: str,
                kiteworks_user: str,
                kiteworks_hostname: str,
                proxy_port: str, 
                proxy_url: str):

      try:
         self.__sftp_access_key = sftp_access_key
         self.__kiteworks_user = kiteworks_user
         self.__kiteworks_hostname = kiteworks_hostname
         self.__proxy_port = proxy_port
         self.__proxy_url = proxy_url

         self.__remote_path = None
         self.__local_path = None
         self.__file_extension = None

         self.__transport = None
         self.sftp_client = None

         if os.path.isfile(self.__sftp_access_key):
            my_PrivateKey = paramiko.RSAKey.from_private_key_file(self.__sftp_access_key)
         else: 
            # In Gitlab pipeline, the "__sftp_access_key" is saved as a variable 
            # in Settings ==> CI/CD ==> variables
            my_PrivateKey = paramiko.RSAKey.from_private_key(io.StringIO(self.__sftp_access_key))
        
         # To avoid this error: An existing connection was forcibly closed by the remote host (10054)
         # try to connect at least 5 times
         count = 0
         while count < 1:
            try:
               logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())
               if self.__proxy_port is None or self.__proxy_url is None:
                  self.__transport = paramiko.Transport((self.__kiteworks_hostname, 22))
                  self.__transport.connect(None, self.__kiteworks_user, None, my_PrivateKey)
                  self.sftp_client = paramiko.SFTPClient.from_transport(self.__transport)
               else:
                  mySock = socks.socksocket()
                  mySock.set_proxy(
                    proxy_type=socks.SOCKS5,
                    addr=self.__proxy_url,
                    port=self.__proxy_port
                  )
                  mySock.settimeout(30)

                  mySock.connect((self.__kiteworks_hostname, 22))
                  self.__transport = paramiko.Transport(mySock)
                  self.__transport.connect(None, self.__kiteworks_user, None, my_PrivateKey)
                  self.sftp_client = paramiko.SFTPClient.from_transport(self.__transport)
               break
            except Exception as err:
               # Connection error - will try again in 30 seconds
               count = count + 1
               if self.sftp_client is not None:
                  self.sftp_client.close()
                  self.sftp_client = None
               if self.__transport is not None:
                  self.__transport.close()
                  self.__transport = None
            sleep(30)

      except Exception as err:
         print(str(err))

   #
   def __enter__(self):
        return self

   #
   def __exit__(self, exc_type, exc_value, traceback):
      if self.sftp_client is not None:
         self.sftp_client.close()
         self.sftp_client = None
      if self.__transport is not None:
         self.__transport.close()
         self.__transport = None



   # Function to download file(s) from Kiteworks
   def download_files(self, 
                      remote_path: str, 
                      local_path: Path, 
                      file_extension: str,
                      move_to_new_location: str = ""):
      try:
         returned_result = ""

         if (self.sftp_client == None):
               returned_result = self.__ERROR_OCCURRED  + self.__NO_SFTP_CLIENT + os.linesep
         else:
            self.__remote_path = remote_path
            self.__local_path = local_path
            self.__file_extension = file_extension

            returned_result = self.__exists_remote(self.__remote_path) 
            if returned_result == "":
               # is it a file?
               if stat.S_ISREG(self.sftp_client.stat(self.__remote_path).st_mode):
                  filename = os.path.basename(self.__remote_path)
                  if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                     full_local_path = os.path.join(self.__local_path, filename)
                     returned_result += self.__get_latest_file(self.__remote_path, full_local_path, move_to_new_location)

               # is it a directory?
               elif stat.S_ISDIR(self.sftp_client.stat(self.__remote_path).st_mode):
                  returned_result = self.__download_files(self.__remote_path, self.__local_path, "", move_to_new_location)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         return returned_result

   
   # Function to download file(s) from Kiteworks
   # A recursive function to download subdirectories as well
   def download_files_recursive(self, 
                      remote_path: str, 
                      local_path: Path, 
                      file_extension: str,
                      move_to_new_location: str = ""):
      try:
         returned_result = ""

         if (self.sftp_client == None):
               returned_result = self.__ERROR_OCCURRED  + self.__NO_SFTP_CLIENT + os.linesep
         else:
            self.__remote_path = remote_path
            self.__local_path = local_path
            self.__file_extension = file_extension

            returned_result = self.__exists_remote(self.__remote_path) 
            if returned_result == "":
               # is it a file?
               if stat.S_ISREG(self.sftp_client.stat(self.__remote_path).st_mode):
                  filename = os.path.basename(self.__remote_path)
                  if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                     full_local_path = os.path.join(self.__local_path, filename)
                     returned_result += self.__get_latest_file(self.__remote_path, full_local_path, move_to_new_location)

               # is it a directory?
               elif stat.S_ISDIR(self.sftp_client.stat(self.__remote_path).st_mode):
                  returned_result = self.__download_files_recursive(self.__remote_path, self.__local_path, "", move_to_new_location)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         return returned_result
      

   # Function to download file(s) from Kiteworks
   def download_files_with_regex(self, 
                                 remote_path: str, 
                                 configurationfile_path: str, 
                                 file_extension: str,
                                 move_to_new_location: str = ""):
      try:
         returned_result = ""

         if (self.sftp_client == None):
               returned_result = self.__ERROR_OCCURRED  + self.__NO_SFTP_CLIENT + os.linesep
         else:
            self.__remote_path = remote_path
            self.__file_extension = file_extension

            returned_result = self.__exists_remote(self.__remote_path) 
            if returned_result == "":
               # is it a file?
               if stat.S_ISREG(self.sftp_client.stat(self.__remote_path).st_mode):
                  filename = os.path.basename(self.__remote_path)
                  if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                     local_path = self.__find_local_path(self.__remote_path, configurationfile_path, self.__file_extension)
                     if local_path and len(local_path) > 0:
                        full_local_path = os.path.join(local_path, filename)
                        returned_result += self.__get_latest_file(self.__remote_path, full_local_path, move_to_new_location)

               # is it a directory?
               elif stat.S_ISDIR(self.sftp_client.stat(self.__remote_path).st_mode):
                  returned_result = self.__download_files(self.__remote_path, "", configurationfile_path, move_to_new_location)

      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         return returned_result


   # Function to upload file(s) to Kiteworks
   def upload_files(self, 
                    remote_path: str, 
                    local_path: Path, 
                    file_extension: str):
      try:
         returned_result = ""

         if (self.sftp_client == None):
               returned_result = self.__ERROR_OCCURRED  + self.__NO_SFTP_CLIENT + os.linesep
         else:
            self.__remote_path = remote_path
            self.__local_path = local_path
            self.__file_extension = file_extension

            # Creates remote folder if it does not exist
            if self.__exists_remote(remote_path) != "":
               self.sftp_client.mkdir(remote_path)

            returned_result = self.__exists_remote(self.__remote_path) 
            if returned_result == "":
               # is it a file?
               if os.path.isfile(self.__local_path):
                  filename = os.path.basename(self.__local_path)
                  if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                     full_remote_path = str(self.__remote_path).rstrip("/") + '/' + filename
                     self.sftp_client.put(self.__local_path, full_remote_path)
                     returned_result = self.__OUTCOME_SUCCESS
               # is it a directory?
               elif os.path.isdir(self.__local_path):
                  returned_result = self.__upload_files_recursive(self.__local_path, self.__remote_path)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         return returned_result

   # Function to remove a file from Kiteworks
   def remove_file(self, 
                   remote_path: str):
      try:
         returned_result = ""

         if (self.sftp_client == None):
               returned_result = self.__ERROR_OCCURRED  + self.__NO_SFTP_CLIENT + os.linesep
         else:
            self.__remote_path = remote_path

            returned_result = self.__exists_remote(self.__remote_path) 
            if returned_result == "":
               # is it a file?
               if stat.S_ISREG(self.sftp_client.stat(self.__remote_path).st_mode):
                  self.sftp_client.remove(self.__remote_path)
                  returned_result = self.__OUTCOME_SUCCESS
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         return returned_result
      

   # Check if the remote directory exists
   def __exists_remote(self, remote_path):
      try:
         returned_result = "" 

         self.sftp_client.stat(remote_path)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + " Remote directory: " + str(remote_path) + os.linesep + str(err)

      return returned_result


   # Searching/matching the pattern of the input "remote_path" to extract the destination local path
   def __find_local_path(self, 
                           remote_path: str, 
                           configurationfile_path: str, 
                           file_extension: str):
      returned_result = ""

      try:
         local_path = ""

         # searching/matching the pattern of the input "remote_path" to extract the destination local path
         regex_pattern_folder = r'^(.*\/)([^\/]*)$'
         sp = re.compile(regex_pattern_folder)
         result = sp.match(remote_path)

         if result and len(result.groups()) > 1:
            remote_folder = result.groups()[0]
            file_name = result.groups()[1]

            # 
            tree = ET.parse(configurationfile_path)
            root = tree.getroot()
            if (root.find("./flows/flow") is not None):
               for flow in root.findall("./flows/flow"):
                  if remote_folder == flow.get('RemotePath'):
                     regex_pattern_file = flow.get('RegEx') + file_extension
                     sp = re.compile(regex_pattern_file)
                     result = sp.match(file_name)
                     if result and len(result.groups()) > 1:
                        local_path = flow.get('LocalPath')
                        break
      except Exception as err:
         local_path = ""
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result
      else:
         if returned_result == "":
            return local_path
         else:
            return returned_result


   # Get the latest file
   def __get_latest_file(self, 
                         full_remote_path, 
                         full_local_path,
                         move_to_new_location):
      try:
         returned_result = "" 

         remote_folderpath = os.path.dirname(full_remote_path)
         remote_filename = os.path.basename(full_remote_path)
         # Change the “current directory” of this self.sftp_client session
         self.sftp_client.chdir(remote_folderpath)

         for remote_file in sorted(self.sftp_client.listdir_attr(), key=lambda k: k.st_mtime, reverse=True):
            if remote_file.filename.endswith(remote_filename):
               if os.path.isfile(full_local_path):
                  if remote_file.st_mtime > os.path.getmtime(full_local_path):
                     os.remove(full_local_path)
                     self.sftp_client.get(remote_file.filename, full_local_path)
                     if len(move_to_new_location) > 0:
                        returned_result = self.__DOWNLOAD_SUCCESS + f'{str(full_local_path)}' + os.linesep
                        returned_result += self.__move_file(full_remote_path, move_to_new_location) + os.linesep
                     else:   
                        returned_result = self.__DOWNLOAD_SUCCESS + f'{str(full_local_path)}' + os.linesep
                     break
                  else:
                     if len(move_to_new_location) > 0:
                        returned_result = "No need to download this file: " + f'{str(full_remote_path)}' + os.linesep
                        returned_result += self.__move_file(full_remote_path, move_to_new_location) + os.linesep
                     else:   
                        returned_result = "No need to download this file: " + f'{str(full_remote_path)}' + os.linesep
                     break
               else:
                  self.sftp_client.get(remote_file.filename, full_local_path)
                  if len(move_to_new_location) > 0:
                     returned_result = self.__DOWNLOAD_SUCCESS + f'{str(full_local_path)}' + os.linesep
                     returned_result += self.__move_file(full_remote_path, move_to_new_location) + os.linesep
                  else:   
                     returned_result = self.__DOWNLOAD_SUCCESS + f'{str(full_local_path)}' + os.linesep
                  break
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result + os.linesep
      else:
         if returned_result == "":
            returned_result = "Could not download this file: " + f'{str(full_remote_path)}' + os.linesep
         return returned_result + os.linesep


   # Move file to new location
   def __move_file(self, current_full_remote_path, move_to_new_location):
      try:
         returned_result = ""

         remote_folderpath = os.path.dirname(current_full_remote_path)
         remote_filename = os.path.basename(current_full_remote_path)

         # Change the “current directory” of this self.sftp_client session to 
         # None, otherwise checking for file or directory below will not work
         self.sftp_client.chdir(None)

         # Construct the destination of the file
         destination_remote_path = str(remote_folderpath).rstrip("/") + '/' + move_to_new_location

         # Creates remote folder if it does not exist
         if self.__exists_remote(destination_remote_path) != "":
            self.sftp_client.mkdir(destination_remote_path)

         destination_remote_path = destination_remote_path + '/' + remote_filename
         self.sftp_client.rename(current_full_remote_path, destination_remote_path)
         returned_result = "File moved to: " + str(destination_remote_path) + os.linesep + os.linesep
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + "Failed to move file: " + str(current_full_remote_path) + ' ' + str(err) + os.linesep + os.linesep

      return returned_result
   

   # A function to download just files (no subdirectories)
   def __download_files(self, 
                                  remote_path: str, 
                                  local_path: str, 
                                  configurationfile_path: str,
                                  move_to_new_location: str):
      try:
         returned_result = ""

         # Creates local folder if it does not exist
         if local_path and not os.path.exists(local_path):
            os.mkdir(local_path)

         for filename in self.sftp_client.listdir(remote_path):
            full_remote_path = str(remote_path).rstrip("/") + '/' + filename

            # Change the “current directory” of this self.sftp_client session to 
            # None, otherwise checking for file or directory below will not work
            self.sftp_client.chdir(None)

            # is it a file?
            if stat.S_ISREG(self.sftp_client.stat(full_remote_path).st_mode):
               if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                  # Regex case
                  if configurationfile_path and not local_path:
                     local_path_temp = self.__find_local_path(full_remote_path, configurationfile_path, self.__file_extension)

                     if local_path_temp and len(local_path_temp) > 0:
                        full_local_path = os.path.join(local_path_temp, filename)
                        # Creates local folder if it does not exist
                        if local_path_temp and not os.path.exists(local_path_temp):
                           os.mkdir(local_path_temp)

                        returned_result += self.__get_latest_file(full_remote_path, full_local_path, move_to_new_location)
                  elif local_path:
                     full_local_path = os.path.join(local_path, filename)
                     returned_result += self.__get_latest_file(full_remote_path, full_local_path, move_to_new_location)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result + os.linesep
      else:
         if returned_result == "":
            returned_result = self.__NO_FILE_TO_DOWNLOAD + f'{str(remote_path)}' + os.linesep
         return returned_result + os.linesep
         

   # A recursive function to download subdirectories as well.
   def __download_files_recursive(self, 
                                  remote_path: str, 
                                  local_path: str, 
                                  configurationfile_path: str,
                                  move_to_new_location: str):
      try:
         returned_result = ""

         # Creates local folder if it does not exist
         if local_path and not os.path.exists(local_path):
            os.mkdir(local_path)

         for filename in self.sftp_client.listdir(remote_path):
            full_remote_path = str(remote_path).rstrip("/") + '/' + filename

            # Change the “current directory” of this self.sftp_client session to 
            # None, otherwise checking for file or directory below will not work
            self.sftp_client.chdir(None)

            # is it a file?
            if stat.S_ISREG(self.sftp_client.stat(full_remote_path).st_mode):
               if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                  # Regex case
                  if configurationfile_path and not local_path:
                     local_path_temp = self.__find_local_path(full_remote_path, configurationfile_path, self.__file_extension)

                     if local_path_temp and len(local_path_temp) > 0:
                        full_local_path = os.path.join(local_path_temp, filename)
                        # Creates local folder if it does not exist
                        if local_path_temp and not os.path.exists(local_path_temp):
                           os.mkdir(local_path_temp)

                        returned_result += self.__get_latest_file(full_remote_path, full_local_path, move_to_new_location)
                  elif local_path:
                     full_local_path = os.path.join(local_path, filename)
                     returned_result += self.__get_latest_file(full_remote_path, full_local_path, move_to_new_location)

            # is it a directory?
            elif stat.S_ISDIR(self.sftp_client.stat(full_remote_path).st_mode):
               returned_result = self.__download_files_recursive(full_remote_path, os.path.join(local_path, filename), configurationfile_path, move_to_new_location)
      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result + os.linesep
      else:
         if returned_result == "":
            returned_result = self.__NO_FILE_TO_DOWNLOAD + f'{str(remote_path)}' + os.linesep
         return returned_result + os.linesep


   # A recursive function to upload subdirectories as well.
   def __upload_files_recursive(self, 
                                local_path, 
                                remote_path):
      try:
         returned_result = ""

         # Creates remote folder if it does not exist
         if self.__exists_remote(remote_path) != "":
            self.sftp_client.mkdir(remote_path)

         for filename in os.listdir(local_path):
            full_local_path = os.path.join(local_path, filename)
            full_remote_path = str(remote_path).rstrip("/") + '/' + filename

            # is it a file?
            if os.path.isfile(full_local_path):
               if os.path.splitext(filename)[-1].lower() == self.__file_extension:
                  self.sftp_client.put(full_local_path, full_remote_path)
                  returned_result = self.__OUTCOME_SUCCESS
            # is it a directory?
            elif os.path.isdir(full_local_path):
               returned_result = self.__upload_files_recursive(full_local_path, full_remote_path)

      except Exception as err:
         returned_result = self.__ERROR_OCCURRED + str(err)
         return returned_result + os.linesep
      else:
         return returned_result + os.linesep
