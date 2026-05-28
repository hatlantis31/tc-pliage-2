# PowerShell script for setting up a Python project environment

# Check if PyCharm is running
$pycharmProcess = Get-Process pycharm* -ErrorAction SilentlyContinue
if ($pycharmProcess -ne $null)
{
    Write-Host "PyCharm is currently running. Please close PyCharm before running this script."
    Write-Host "Press any key to exit..."
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}
else
{
    Write-Host "PyCharm is not running. You can proceed with the script."
}

# Attempt to find the newest Python version installed that is 3.8 or above
$pythonCommandCandidates = @("python3.10", "python3.12", "python3.11", "python3.9", "python3.8", "python3", "python") # Ordered by preference
$newestPythonVersionCommand = $null
$minimumRequiredVersion = [Version]"3.8"

foreach ($python in $pythonCommandCandidates)
{
    # Try executing the Python command to get its version
    $versionString = & $python --version 2>&1
    if ($versionString -match "Python (\d+\.\d+)")
    {
        $version = $matches[1]
        if ([Version]$version -ge $minimumRequiredVersion)
        {
            $newestPythonVersionCommand = $python
            break # Exit the loop once the suitable version is found
        }
    }
}

if ($newestPythonVersionCommand -eq $null)
{
    Write-Host "No suitable Python installation found. Please ensure you have Python 3.8 or newer installed."
    exit
}

Write-Host "Newest suitable Python version command found: $newestPythonVersionCommand"

# Define the virtual environment directory name
$venvDirName = ".\venv"

# Check for Virtual Environment Directory
if (-Not (Test-Path $venvDirName))
{
    Write-Host "Virtual environment directory not found. Attempting to create a new virtual environment."
    & $newestPythonVersionCommand -m venv $venvDirName
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "Virtual environment created successfully with $newestPythonVersionCommand."
    }
    else
    {
        Write-Host "Failed to create the virtual environment. Please check your Python installation."
        exit
    }
}
else
{
    Write-Host "Virtual environment directory already exists."
}

# Attempt to activate the Virtual Environment
$venvScriptPath = Join-Path -Path $venvDirName -ChildPath "Scripts\Activate.ps1"
try
{
    Write-Host "Activating the virtual environment..."
    & $venvScriptPath
    Write-Host "Virtual environment activated."
}
catch
{
    Write-Host "Failed to activate the virtual environment. Please ensure the virtual environment is correctly set up."
    exit
}

# Install packages from requirements.txt
$reqFilePath = ".\requirements.txt"
if (Test-Path $reqFilePath)
{
    Write-Host "Installing packages from requirements.txt..."
    & $newestPythonVersionCommand -m pip install -r $reqFilePath
    if ($LASTEXITCODE -eq 0)
    {
        Write-Host "Packages installed successfully."
    }
    else
    {
        Write-Host "Failed to install packages. Please check the requirements.txt file and your Python environment."
        exit
    }
}
else
{
    Write-Host "requirements.txt not found. Please ensure it exists in the main folder and try again."
}

Write-Host "Environment setup is complete."
Write-Host "Please complete the setup in PyCharm by following these steps:"
Write-Host "1. Open your project in PyCharm."
Write-Host "2. Go to `File -> Settings -> Project: YourProjectName -> Python Interpreter`."
Write-Host "3. Choose the Python interpreter located in your project's 'venv' directory."
Write-Host "4. To set run arguments for '__main__.py', go to `Run -> Edit Configurations`."
Write-Host "5. Select '__main__' from the list or create a new configuration if it doesn't exist."
Write-Host "6. In the 'Script path' field, ensure it points to '__main__.py' in your project directory."
Write-Host "7. In the 'Parameters' field, enter `--log_level INFO --debug True`."
Write-Host "8. Click 'Apply' and then 'OK' to save your configuration."
Write-Host "You can now run '__main__.py' with the specified arguments from within PyCharm."

# Example of showing instructions as a pop-up message using a MessageBox in Windows
Add-Type -AssemblyName PresentationFramework
[System.Windows.MessageBox]::Show("Please complete the setup in PyCharm:`n1. Open your project in PyCharm.`n2. Go to File -> Settings -> Project: YourProjectName -> Python Interpreter.`n3. Choose the Python interpreter located in your project's 'venv' directory.`n4. To set run arguments for '__main__.py', go to Run -> Edit Configurations.`n5. Select '__main__' from the list or create a new configuration if it doesn't exist.`n6. In the 'Script path' field, ensure it points to '__main__.py' in your project directory.`n7. In the 'Parameters' field, enter --log_level INFO --debug True.`n8. Click 'Apply' and then 'OK' to save your configuration.`nYou can now run '__main__.py' with the specified arguments from within PyCharm.", "Setup Instructions")