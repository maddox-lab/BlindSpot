# *BlindSpot*

**Author: Jenna Vesey**  (@Jenna-VC)

**Link to project:** https://github.com/maddox-lab/blindspot

**Intended use:** This app looks to create a reproducible pipeline for researchers to blind data / image files. It is designed for blinding experimental datasets prior to analysis to reduce bias. The easy-to-use GUI interface is cross-compatible with macOS and Windows, allowing for easy, reproducible access to blinding various file types. BlindSpot modifies filenames only and does not alter file contents. 

**For questions and Issues:** Please post an issues request on GitHub or email jennavc@unc.edu. 


**Current version:** 1.0

*Previous iterations of the code are available upon request* 


## Latest releases:

Windows: *Updated once the final one is confirmed*

Mac: *Updated once the final one is confirmed*


## How It's Made:

**Tech used:** Python 3.14

This app was created based on a blinding code that an undergraduate developed at UNC Chapel Hill in Dr. Amy Maddox's Lab. The full code was written and turned into an app by Jenna Vesey. The goal of this project was to streamline blinding and make it easily accessible to anyone who does research but does not have prerequisite Python knowledge. 


The entire program was built using Python in VS Code. The program uses Tkinter to wrap it into an easy GUI interface for easy access and distribution for users. The program was tested using the pytest package in order to determine that the code and functions work as intended. For more information about construction of software, please read the associated paper. 


## Installation

BlindSpot can be downloaded as a zipped .exe file (Windows) or a zipped .app file (macOS) from this gihub repository. If this is the perferred method of download, no python or installation of any packages are required for use. Exe files will be updated and downloaded from the release folder for the latest version. It also can be used with the command line feature. Please go to the **To Use: (Command Line)**  section below in order to see intallation and use instructions. 

The original package of code is located is available on the repository as well. The author has previous versions that are available upon request. This code was compiled using PyInstaller on the command line and was tested with the attached pytest codes. This requires the packages: os, csv, uuid, time, shutil, random, threading, pathlib, tkinter, datetime, webbrowser, and sys. All of these packages are compatible with Python v 3.13. 

## To Use (GUI):

User clicks and open the respective exe/app file and the program GUI launches. 

---

### Blinding Function

_This function selected at the top blinds file data_


1) User inputs
   - **Target Folder:**  The folder containing the files to be blinded
   - **File Extension:** The user types in the file extension of their choice (i.e. tif, png, jpeg, nd2, txt, etc.). This does not require a period but is spelling specific
   - **Output Organization:** Grants the user the option to move all the blinded files into one folder
   - **Preserve Original File Names:** Grants the user the option to keep the original files in the original location and create a blinded copy. If this option is not selected, a warning message will pop up encouraging it to be saved or the files will be rewritten. The user has to actively decide to continue the run regardless. It is recommended to have a backup prior to running this program. 
   - **Subfolder Search:** Allows the user to include all subfolders within the specified directory
  


2) User hits run and the program starts
   - If safe mode is not checked, the file will put up a pop up box saying: "Warning: BlindSpot. This will rename/move files with the target extension. If safe mode is OFF, original names won't remain. Continue?". The user has to press okay to continue, if they do not want this, pressing cancel brings the user back to the main page. 


3)  Loading bar shows progress and estimates finishing time



4) A pop up comes up demonstrating the results of the run:
   - **Blinding Done!**
   - **Base Folder:** The name of the full path of the selected target folder
   - **Total Files:** The total number of files identified and processed
   - **Blinded moved/renamed**: Number of files that were moved the blind folder
   - **Blinded Copied:** How many files were blinded
   - **Already Done Skipped:** Checks if the files were already blinded, and if they were, it skips this
   - **Errors skipped:** Number of files skipped because of errors processing the file(s)
   - **Crash Recovery: finalized, aborted, lost -** returns the amount of successfully processed, aborted, or lost files on a rerun in case of a crash
   - **Elasped:** The amount of time it took
   - **Mappings:** How many mappings were created between the blinded file name and the original file name



5) A fun randomly generated quote / pop culture message appears in it's own pop up box


6) User has two logs in the original speicifed folder:
   - **_blinding_log.csv:** The crash protection log with all actions saved
   - **Blinding_Key.csv:** The easy to read key that allows translations from old file name to new file name. It also maps the original path name to be saved.
  
---

### Unblinding Function

_This function selected at the top unblinds the blinded file data produced by BlindSpot_


1) User inputs
   - **Target Folder:**  The folder containing the files to be unblinded
   - **Blinding Key:** The user gives the blinding key path for the associated blinded files in order to unblind the name of the files. 
   - **Output Organization:** Grants the user the option to move all the unblinded files into a specificed location
   - **Overwrite if exists:** If the original file name exists in the given output, if this is selected, the unblinded file replaces the original one. If it is unblinded, it skips it if it exists in the directory. 
  


2) User hits run and the program starts


4)  Loading bar shows progress and estimates finishing time



5) A pop up comes up demonstrating the results of the run:
   - **Unlinding Done!**
   - **Base Folder:** The path of the folder where the original blinded files were
   - **Key CSV:** The path for the blinding key generated by the blinding function
   - **Unblinded Files:** The path for where the unblinded files ended up
   - **Toal number of files**: Number of files that were identified in the key
   - **Number of files unblinded::** How many files were unblinded
   - **Number of Files missing (skipped):** Files that were missing for the folder and were not unblinded
   - **Skipped - files already exist:** Number of files skipped because the unblinded name file already exists in that folder
   - **Errors:** Returns how many errors the program ran into while unblinding the data
   - **Log:** The location of _blinding_log.csv



6) A fun randomly generated quote / pop culture message appears in it's own pop up box


7) User has one logs in the user specified unblinded file folder:
   - **_unblinding_log.csv:** A log of the unblinding command that demonstrates errors and shows conversion if needed by the user 


## To Use (Command Line):

This section shows how _BlindSpot_ can be implemented into command line functionality. 

---

When the information is downloaded from the github for all the program. If the user navigates to the BlindSpot folder containing the spec and toml file, they can add it to their path using ```pip3 install -e . ```. This indicates that the program will add the command line function to their terminal. 

When run from the terminal, the following commands are present and can be found by running the command ``` blindspot --help ```: 

              BlindSpot — The Amy Maddox Lab, UNC Chapel Hill
              Command Line Usage:

              blindspot                          Open the GUI
              blindspot --blinder [options]      Blind files from the command line
              blindspot --unblinder [options]    Unblind files from the command line

              Blinder options:
                --base_path PATH       Folder containing files to blinded (required)
                --extension EXT        File extension to blind, e.g. nd2 (required)
                --move_to_blind        Move files to a 'Blind Files' folder
                --clone_og             Copy originals before blinding (safe mode) *Recommended*
                --include_subdirs      Include subfolders within specified directory

            Unblinder options:
                --base_folder PATH     Folder containing blinded files (required)
                --blinding_key PATH    Path to Blinding_Key.csv (required)
                --move_unblind_to PATH Destination folder for unblinded files
                --overwrite            Overwrite existing files



            Examples:
              blindspot --blinder --base_path C:/data --extension nd2 --clone_og
              blindspot --unblinder --base_folder C:/data --blinding_key C:/data/Blinding_Key.csv




## Technical Workflow of the code

This shows the step by step for the technical side of the code instead of the user's workflow for reference

---


### Blinding Program technical workflow 


### 1) User Input via the user interface

When the app is launched, the user is prompted to provide the following inputs: 
  - **Target Folder:**  The folder containing the files to be blinded
   - **File Extension:** The user types in the file extension of their choice (i.e. tif, png, jpeg, nd2, txt, etc.). This does not require a period but is spelling specific
   - **Output Organization:** Grants the user the option to move all the blinded files into one folder
   - **Preserve Original File Names:** Grants the user the option to keep the original files in the original location and create a blinded copy. If this option is not selected, a warning message will pop up encouraging it to be saved or the files will be rewritten. The user has to actively decide to continue the run regardless. It is recommended to have a backup prior to running this program. 
   - **Subfolder Search:** Allows the user to include all subfolders within the specified directory

The goal of this is to allow the user to customize their blinding process based on their specific needs.  



### 2) Preprocessing and Validation

After the user clicks submit, the program performs some validation steps:

   - Confirms files of the specified type exist in the specified directory
   - Automatically appends a '.' to the file extension if the user did not add it
   - Corrects file-extension case sensitivity
   - Halts the program if no files of the specified type are found in the folder


Once the program finishes these steps, the program initializes required variables. 


Important Implementation details:
   - Path files are managed using pathlib to ensure cross-platform compatibility
   - File discovery uses glob, also allowing cross-platform compatibility
   - All relevant file paths are stored internally with the data if they will be copied or moved


Two CSV files are created at this stage: 
   - _blinding_log.csv
   - Blinding_Key.csv




### 3) File Processing and Blinding 

For each file identified:
   - The program checks _blinding_log.csv to make sure the specified file has not already been blinded
   - If selected, the original file is duplicated to protect the original location and name of the initial file
   - Files are renamed using the UUID package, keeping the final 8 digits of the UUID in order to keep it random but concise




### 4) Logging and Progress Tracking

During the execution of the program, the application:

   - Tracks and records time steps for each of the blinding stages
   - Updates the progress bar to provide an easy way to let the user know how many are done
   - Only commits file name changes when the file is considered "done"

All of these actions are incrementally saved into _blinding_log.csv



### 5) Output 

On completion of the run, two CSV files are saved in the original specified directory

##### _blinding_log.csv 

Records a detailed trail of the code, including:
   - Timestamp
   - Original File Path
   - Original File Name
   - New Blinded File Name
   - Action type (Starting, keyed, copied, moved, pending, error, aborted, lost, finalized, and done)
   - File location in the full file path

##### Action type terms 

   - Starting: The start of the file run
   - Keyed: File given a blind name 
   - Copied: Original is copied to its original path
   - Moved: File relocated to the 'Blind Files' folder if the user selected this
   - Pending: Intermediate step logged in case of a crash
   - Error: File processing failed
   - Aborted: A file had an issue and the software skips it without crashing 
   - Lost: The file and the rename are unable to be located by the code (recommend maintaining a backup)
   - Finalized: After a crash, files that were only partially finished processing successfully get reprocessed on a rerun
   - Done: All requested actions have been completed successfully


##### Blinding_Key.csv

Contains 
   - Original File Name
   - Corresponding Blinded File Name
   - Path of the original file in relation to the parent directory for easy tracking



### 6) Post-Blinding 

Afterwards, the user can map their newly blinded files to the Blinding_key.csv to determine the corresponding original file name when unblinding is required. The result is a reproducible and user-friendly blinding pipeline suitable for experimental data handling. 

---

### Unblinding Program technical workflow 

### 1) User Input via the user interface

When the app is launched, the user is prompted to provide the following inputs: 
   - **Target Directory:**  The folder containing the files to be unblinded
   - **Blinding Key Location:** User uploads the blinding key for that specific file folder
   - **Output Organization:** Grants the user the option to move the unblinded folder 
   - **Preserve Original File Names:** The unblinded file can replace the original ones if they are in the same folder so there are not two copies

The goal of this is to allow the user to easily unblind the blinded data files within a specific directory and move to an organized structure. 



### 2) Preprocessing and Validation

After the user clicks submit, the program undergoes a series of steps. 

   - Confirms files in the folder are found in the blinding key
   - Loops through all subdirectories for confirmation
   - Creates the unblinding log if it does not exist

Once the program finishes these steps, the program initializes and gets ready to run. 


Important Implementation details:
   - Path files are managed using pathlib to ensure cross-platform compatibility
   - File discovery uses glob, also allowing cross-platform compatibility
   - All relevant file paths are stored internally with the data if they will be copied or moved




### 3) File Processing and Unblinding 

For each file identified:
   - The program checks _unblinding_log.csv to make sure the specified file has not already been unblinded and skips
   - Compares all the files in the folder to the Blinding_Key.csv and determines which need to be unblinded within that specified directory
   - It then will rename the file with original unblinded name and move it to the specified directory
   - The unblinding log is updated and the the file is tracked

### 5) Output 

On completion of the run, the _unblinding_log.csv

##### _uncblinding_log.csv 

Records a detailed trail of the code, including:
   - Timestamp
   - Old File Path: The location of the blinded file 
   - Old File Name: The name of the blinded file
   - New file name: the name of the Unblinded file aka the original file name
   - Action type (Unblinded, error skipped, error missing)
   - Message of error or if it is unblinded

##### Action type terms 

   - Unblinded: If the file has been succesfully unblinded
   - Error Skipped: If the file has already been unblinded, the program skips it
   - Error missing: If the file is missing the program will sikp it 

### 6) Post-Unblinding 

The user can see the log where the unblinded files are and see if they were unblinded. It can be compared to the blinding key to guarentee accuracy. 


## Citations:

If you use BlindSpot in your research, please cite it at: *insert Micropub citation*


## Important Notes:

1) Users are strongly encouraged to maintain backups prior to use. 
2) Some of the fun quotes at the end are from pop culture. I take no ownership of those quotes and they belong to their respective creators.
3) If Microtubules being the best cytoskeleton element at the end makes you sad, please note that the person who oversaw this being published insisted it stayed.
4) This does not change actual image data acquired, so to maximize its efficacy, please try to keep imaging procedures as uniform as possible to help decrease bias as much as possible.
5) Future updates will avoid updating the structure of the blinding_key.csv file, attempting to keep any parts of the workflow more consistant. 


## Acknowledgements:

This version of the code was written by Jenna Vesey. The code was inspired by Siddharth Sankaranarayanan's original blinding code. 

Code was developed in the Amy Maddox Lab at UNC Chapel Hill

The Maddox Lab website can be accessed via this link: https://asmlab.web.unc.edu/

I would like to give a special thank you to Linnea Wethekam, Amy Liu, and Siddharth Sankaranarayanan for their testing, feedback, and support.

LICENSE: MIT License
