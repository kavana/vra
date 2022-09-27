#
# Copyright (c) 2022 VMware, Inc. All Rights Reserved.
#

from github import Github
import json
import logging
import math

# Constants
GITHUB_ENTERPRISE_LOG_PREFIX = 'github-enterprise-integration'
AUTH_LINK_KEY = 'privateKey'
VERIFY_SSL_CERTS = False  # By default do not verify certs (TODO: WE WILL NEED TO REVISIT THIS!)

# Inputs
INPUT_AUTH_CREDENTIALS_LINK = 'authCredentialsLink'
INPUT_BASE_URL = 'baseUrl'
INPUT_LOG_LEVEL = 'logLevel'
INPUT_REPOSITORY_NAME = 'repositoryName'
INPUT_PROJECT_NAME = 'projectName'
INPUT_FILE_PATH = 'filePath'
INPUT_BRANCH_NAME = 'branchName'
INPUT_DIR_PATH = 'dirPath'
INPUT_TO_COMMIT = 'toCommit'
INPUT_FILE_SIZE_LIMIT = 'fileSizeLimit'
INPUT_PAGE = 'page'
INPUT_PAGE_SIZE = 'pageSize'
INPUT_SKIP_COMMIT_INFO = 'skipCommitInfo'

# Outputs
OUTPUT_ERROR_MESSAGE = 'error_message'
OUTPUT_STATUS = 'status'
OUTPUT_STATUS_SUCCESS = 'success'
OUTPUT_STATUS_FAILURE = 'failure'
OUTPUT_RESULT = 'result'
OUTPUT_ENCODING = 'encoding'
OUTPUT_CONTENT = 'content'
OUTPUT_FILE_NAME = 'fileName'
OUTPUT_FILE_PATH = 'filePath'
OUTPUT_AUTHOR_NAME = 'authorName'
OUTPUT_COMMITTER_NAME = 'committerName'
OUTPUT_COMMITTER_EMAIL = 'committerEmail'
OUTPUT_COMMIT_ID = 'commitId'
OUTPUT_COMMIT_DATE = 'commitDate'
OUTPUT_COMMITS = 'commits'
OUTPUT_COMMENTS = 'comments'
OUTPUT_FILE_ACTION = 'fileAction'
OUTPUT_PREV_FILE_NAME = 'previousFileName'
OUTPUT_TOTAL_PAGES = 'totalPages'
OUTPUT_TOTAL_ELEMENTS = 'totalElements'


def validateToken(context, inputs):

    '''
    Validate GitHub Enterprise Server credentials
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
        * OUTPUT_RESULT bool : Whether the credentials have been authenticated or not
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Validating GitHub Enterprise Server credentials...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Validating GitHub Enterprise Server credentials - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK])
        baseUrl = inputs[INPUT_BASE_URL]
        authCredentialsLink = inputs.get(INPUT_AUTH_CREDENTIALS_LINK, None)

        token = getTokenFromAuthCredentialsLink(context, authCredentialsLink)

        g = Github(base_url = baseUrl, login_or_token = token, verify = VERIFY_SSL_CERTS)

        # Credentials won't be checked until an API call is made. This will either work silently or throw an exception
        g.get_user().name

        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Successfully validated GitHub Enterprise Server credentials')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
        outputs[OUTPUT_RESULT] = True
    except Exception as e:
        errorMessage = f'Failed to validate GitHub Enterprise Server credentials: {str(e)}'
        logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] {errorMessage}')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_ERROR_MESSAGE] = errorMessage
        outputs[OUTPUT_RESULT] = False

    logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Validating GitHub Enterprise Server credentials - outputs: [{str(outputs)}]')
    return outputs


def commitFilesToRepo(context, inputs):

    return


def getFile(context, inputs):

    '''
    Get a file from a GitHub Enterprise repository
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
        * INPUT_REPOSITORY_NAME str : Repository name
        * INPUT_PROJECT_NAME str : Project name
        * INPUT_FILE_PATH str : Full path to the file including file name
        * INPUT_BRANCH_NAME str : The name of the branch
        * INPUT_FILE_SIZE_LIMIT str : Size limit in bytes
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_ENCODING str = The encoding for the file (e.g. 'utf8')
        * OUTPUT_CONTENT str = The encoded file content
        * OUTPUT_FILE_NAME str = The file name
        * OUTPUT_FILE_PATH str = The file path
        * OUTPUT_AUTHOR_NAME str = The author name for the most recent commit of the file.
        * OUTPUT_COMMITTER_NAME str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMITTER_EMAIL str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMIT_ID str = The SHA for the most recent commit of the file.
        * OUTPUT_COMMIT_DATE str = The last modified date of the file. Same as the file's most recent commit date.
        * OUTPUT_COMMENTS str = The commit message.
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting file from GitHub Enterprise Server...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting file from GitHub Enterprise Server - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK, INPUT_REPOSITORY_NAME, INPUT_PROJECT_NAME, INPUT_FILE_PATH, INPUT_BRANCH_NAME, INPUT_FILE_SIZE_LIMIT])
        baseUrl = inputs[INPUT_BASE_URL]
        authCredentialsLink = inputs.get(INPUT_AUTH_CREDENTIALS_LINK, None)
        projectPath = inputs[INPUT_REPOSITORY_NAME] + "/" + inputs[INPUT_PROJECT_NAME]
        filePath = inputs[INPUT_FILE_PATH]
        branchName = inputs[INPUT_BRANCH_NAME]
        fileSizeLimit = inputs[INPUT_FILE_SIZE_LIMIT]

        token = getTokenFromAuthCredentialsLink(context, authCredentialsLink)

        g = Github(base_url = baseUrl, login_or_token = token, verify = VERIFY_SSL_CERTS)
        repo = g.get_repo(projectPath)
        file = repo.get_contents(path=filePath, ref=branchName)

        if file.size > int(fileSizeLimit):
            logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] File size exceeds configured limit.')

            outputs[OUTPUT_ERROR_MESSAGE] = f"File size exceeds configured limit of {fileSizeLimit} bytes."
            outputs[OUTPUT_RESULT] = False
        else:
            logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Found file [{filePath}] in [{projectPath}] on branch [{branchName}]')

            latestFileCommit = repo.get_commits(path=filePath)  # Gets commits that contain this filePath
            commit = latestFileCommit[0].commit  # Gets the GitCommit object from the Commit object

            outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
            outputs[OUTPUT_ENCODING] = file.encoding
            outputs[OUTPUT_CONTENT] = file.content
            outputs[OUTPUT_FILE_NAME] = file.name
            outputs[OUTPUT_FILE_PATH] = file.path
            outputs[OUTPUT_AUTHOR_NAME] = commit and commit.author and commit.author.name
            outputs[OUTPUT_COMMIT_ID] = commit.sha
            outputs[OUTPUT_COMMIT_DATE] = commit.last_modified
            outputs[OUTPUT_COMMENTS] = commit.message

            if commit and commit.committer:
                outputs[OUTPUT_COMMITTER_NAME] = commit.committer.name
                outputs[OUTPUT_COMMITTER_EMAIL] = commit.committer.email

    except Exception as e:
        errorMessage = f'Failed to get file from GitHub Enterprise Server: {str(e)}'
        logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] {errorMessage}')
        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_ERROR_MESSAGE] = errorMessage

    return outputs


def getLatestCommitId(context, inputs):

    '''
    Get the SHA of the latest commit for the given repo, project, and branch
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
        * INPUT_REPOSITORY_NAME str : Repository name
        * INPUT_PROJECT_NAME str : Project name
        * INPUT_BRANCH_NAME str : The name of the branch
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
        * OUTPUT_RESULT str : The SHA of the latest commit
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting latest commit ID from GitHub Enterprise Server...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting latest commit ID from GitHub Enterprise Server - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK, INPUT_REPOSITORY_NAME, INPUT_PROJECT_NAME, INPUT_BRANCH_NAME])
        baseUrl = inputs[INPUT_BASE_URL]
        authCredentialsLink = inputs.get(INPUT_AUTH_CREDENTIALS_LINK, None)
        projectPath = inputs[INPUT_REPOSITORY_NAME] + "/" + inputs[INPUT_PROJECT_NAME]
        branchName = inputs[INPUT_BRANCH_NAME]

        token = getTokenFromAuthCredentialsLink(context, authCredentialsLink)

        g = Github(base_url = baseUrl, login_or_token = token, verify = VERIFY_SSL_CERTS)
        repo = g.get_repo(projectPath)
        branch = repo.get_branch(branch=branchName)
        commit = branch.commit  # Gets the HEAD commit for the branch
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Found HEAD commit for branch [{branchName}]')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
        outputs[OUTPUT_RESULT] = commit.sha

    except Exception as e:
        errorMessage = f'Failed to get latest commit ID from GitHub Enterprise Server: {str(e)}'
        logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] {errorMessage}')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_ERROR_MESSAGE] = errorMessage
        outputs[OUTPUT_RESULT] = ''

    return outputs


def validateSourceControlConfiguration(context, inputs):

    '''
    Get a list of files and commit details under the directory path up to toCommit (or latest on branch if toCommit is not provided.)
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
        * INPUT_REPOSITORY_NAME str : Repository name
        * INPUT_PROJECT_NAME str : Project name
        * INPUT_BRANCH_NAME str : The name of the branch
        * INPUT_DIR_PATH str : The path to the directory from which to get files
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
        * OUTPUT_RESULT bool : Whether the source control configuration is valid or not
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Validating source control configuration from GitHub Enterprise Server...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Validating source control configuration from GitHub Enterprise Server - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK, INPUT_REPOSITORY_NAME, INPUT_PROJECT_NAME, INPUT_BRANCH_NAME])

        inputs[INPUT_SKIP_COMMIT_INFO] = True
        inputs[INPUT_PAGE] = 0
        inputs[INPUT_PAGE_SIZE] = 1

        result = getFiles(context, inputs)

        if (OUTPUT_TOTAL_ELEMENTS in result and result[OUTPUT_TOTAL_ELEMENTS] > 0):
            outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
            outputs[OUTPUT_RESULT] = True
        else:
            outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
            outputs[OUTPUT_RESULT] = False

    except Exception as e:
        errorMessage = f'Failed to validating source control configuration from GitHub Enterprise Server: {str(e)}'
        logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] {errorMessage}')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_ERROR_MESSAGE] = errorMessage
        outputs[OUTPUT_RESULT] = False

    return outputs

def compareCommits(context, inputs):

    return


def getAllCommits(context, inputs):

    '''
    Get the list of all commits for the given given repository, path, and branch.
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
        * INPUT_REPOSITORY_NAME str : Repository name
        * INPUT_PROJECT_NAME str : Project name
        * INPUT_BRANCH_NAME str : The name of the branch
        * INPUT_FILE_PATH str : The file path
        * INPUT_PAGE int : The requested page of commits
        * INPUT_PAGE_SIZE int : The number of commits in each page
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_AUTHOR_NAME str = The author name for the most recent commit of the file.
        * OUTPUT_COMMITTER_NAME str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMITTER_EMAIL str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMIT_ID str = The SHA for the most recent commit of the file.
        * OUTPUT_COMMIT_DATE str = The last modified date of the file. Same as the file's most recent commit date.
        * OUTPUT_COMMENTS str = The commit message.
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting latest commit ID from GitHub Enterprise Server...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting latest commit ID from GitHub Enterprise Server - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK, INPUT_REPOSITORY_NAME, INPUT_PROJECT_NAME, INPUT_BRANCH_NAME, INPUT_FILE_PATH, INPUT_PAGE, INPUT_PAGE_SIZE])
        baseUrl = inputs[INPUT_BASE_URL]
        authCredentialsLink = inputs.get(INPUT_AUTH_CREDENTIALS_LINK, None)
        projectPath = inputs[INPUT_REPOSITORY_NAME] + "/" + inputs[INPUT_PROJECT_NAME]
        branchName = inputs[INPUT_BRANCH_NAME]

        token = getTokenFromAuthCredentialsLink(context, authCredentialsLink)

        g = Github(base_url = baseUrl, login_or_token = token, verify = VERIFY_SSL_CERTS)
        repo = g.get_repo(projectPath)
        branch = repo.get_branch(branch=branchName)

        # Get all commits for the file path


        # Determine which to return based on page / page size


        # Return list of commits


        commit = branch.commit  # Gets the HEAD commit for the branch
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Found HEAD commit for branch [{branchName}]')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS
        outputs[OUTPUT_RESULT] = commit.sha

    except Exception as e:
        errorMessage = f'Failed to get latest commit ID from GitHub Enterprise Server: {str(e)}'
        logging.error(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] {errorMessage}')

        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_ERROR_MESSAGE] = errorMessage
        outputs[OUTPUT_RESULT] = ''

    return outputs


def getCommitInfo(context, inputs):

    return


def downloadRepo(context, inputs):

    return


def getFiles(context, inputs):

    '''
    Get a list of files and commit details under the directory path up to toCommit (or latest on branch if toCommit is not provided.)
    Parameters
    ----------
    context hash : ABX execution context
    inputs hash :
        * INPUT_BASE_URL str : GitHub Enterprise Server URL
        * INPUT_AUTH_CREDENTIALS_LINK str : Auth credentials link
        * INPUT_REPOSITORY_NAME str : Repository name
        * INPUT_PROJECT_NAME str : Project name
        * INPUT_BRANCH_NAME str : The name of the branch
        * INPUT_DIR_PATH str : The path to the directory from which to get files
        * INPUT_TO_COMMIT str : The sha of the commit up to which we'll retrieve files. (will use branch name if not provided)
        * INPUT_PAGE int : The requested page of commits
        * INPUT_PAGE_SIZE int : The number of commits in each page
        * INPUT_SKIP_COMMIT_INFO bool : Skip commit info when collecting files (default to True)
    Returns
    -------
    outputs hash :
        * OUTPUT_STATUS str : Status of the action (either OUTPUT_STATUS_SUCCESS or OUTPUT_STATUS_FAILURE)
        * OUTPUT_FILE_NAME str : The name of the file
        * OUTPUT_FILE_PATH str : The path to the file
        * OUTPUT_ENCODING str = The encoding for the file (e.g. 'utf8')
        * OUTPUT_CONTENT str = The encoded file content
        * OUTPUT_AUTHOR_NAME str = The author name for the most recent commit of the file.
        * OUTPUT_COMMITTER_NAME str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMITTER_EMAIL str = The committer name for the most recent commit of the file.
        * OUTPUT_COMMIT_ID str = The SHA for the most recent commit of the file.
        * OUTPUT_COMMIT_DATE str = The last modified date of the file. Same as the file's most recent commit date.
        * OUTPUT_COMMENTS str = The commit message.
        * OUTPUT_FILE_ACTION str = The action performed on this file (e.g., ADDED, UPDATED, DELETED)
        * OUTPUT_PREV_FILE_NAME str = The previous file name is provided if the file action is renamed.
        * OUTPUT_ERROR_MESSAGE str : Error message in case the action status is OUTPUT_STATUS_FAILURE
    '''

    outputs = {}
    setup(inputs)

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting list of files from GitHub Enterprise Server...')
        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Getting list of files from GitHub Enterprise Server - inputs: [{str(inputs)}]')

        validateInputs(inputs, [INPUT_BASE_URL, INPUT_AUTH_CREDENTIALS_LINK, INPUT_REPOSITORY_NAME, INPUT_PROJECT_NAME, INPUT_BRANCH_NAME, INPUT_PAGE, INPUT_PAGE_SIZE])
        baseUrl = inputs[INPUT_BASE_URL]
        authCredentialsLink = inputs.get(INPUT_AUTH_CREDENTIALS_LINK, None)
        projectPath = inputs[INPUT_REPOSITORY_NAME] + "/" + inputs[INPUT_PROJECT_NAME]
        branchName = inputs[INPUT_BRANCH_NAME]
        dirPath = inputs[INPUT_DIR_PATH] if INPUT_DIR_PATH in inputs and len(inputs[INPUT_DIR_PATH]) != 0 else None
        toCommit = inputs[INPUT_TO_COMMIT] if INPUT_TO_COMMIT in inputs and len(inputs[INPUT_TO_COMMIT]) != 0 else None
        shaOrBranch = toCommit or branchName
        shaOrBranchAndDirPath = shaOrBranch + (":" + dirPath if dirPath else "")
        skipCommitInfo = inputs[INPUT_SKIP_COMMIT_INFO] if INPUT_SKIP_COMMIT_INFO in inputs else True
        pageNumber = int(inputs[INPUT_PAGE])
        pageSize = int(inputs[INPUT_PAGE_SIZE])

        token = getTokenFromAuthCredentialsLink(context, authCredentialsLink)

        g = Github(base_url = baseUrl, login_or_token = token, verify = VERIFY_SSL_CERTS)
        repo = g.get_repo(projectPath)
        gitTree = repo.get_git_tree(shaOrBranchAndDirPath, True)
        targetFiles = []

        logging.info(f'Get all files under directory [{dirPath}] in [{shaOrBranchAndDirPath}] page number is [{pageNumber}] and page size is [{pageSize}]')

        # Get only file types (i.e.blob) and sort by file path
        for element in gitTree.tree:
            if element.type == 'blob':
                targetFiles.append(element.path)

        targetFiles.sort()

        outputs[OUTPUT_TOTAL_PAGES] = math.ceil(len(targetFiles) / pageSize)
        outputs[OUTPUT_TOTAL_ELEMENTS] = len(targetFiles)
        filesToReturn = getPagedSlice(pageNumber, pageSize, targetFiles)
        outputs[OUTPUT_CONTENT] = []

        # 3. Iterate file paths in the paginated sublist and save name, path, and latest commit before toCommit.
        for filePath in filesToReturn:
            content = {}
            content[OUTPUT_FILE_NAME] = filePath if filePath.find('/') == -1 else filePath[filePath.rfind('/') + 1:]
            content[OUTPUT_FILE_PATH] = filePath
            content[OUTPUT_COMMITS] = []

            if not skipCommitInfo:
                commitInfo = {}
                fullPath = dirPath + "/" + filePath if dirPath else filePath
                file = repo.get_contents(path=fullPath, ref=shaOrBranch)
                commit = {}

                if toCommit:
                    commit = repo.get_commit(toCommit).commit
                else:
                    latestFileCommit = repo.get_commits(path=fullPath)  # Gets commits that contain this filePath
                    commit = latestFileCommit[0].commit  # Gets the GitCommit object from the Commit object

                commitInfo[OUTPUT_ENCODING] = file.encoding
                commitInfo[OUTPUT_CONTENT] = file.content
                commitInfo[OUTPUT_AUTHOR_NAME] = commit and commit.author and commit.author.name
                commitInfo[OUTPUT_COMMIT_ID] = commit.sha
                commitInfo[OUTPUT_COMMIT_DATE] = commit.last_modified
                commitInfo[OUTPUT_COMMENTS] = commit.message

                if commit and commit.committer:
                    commitInfo[OUTPUT_COMMITTER_NAME] = commit.committer.name
                    commitInfo[OUTPUT_COMMITTER_EMAIL] = commit.committer.email

                content[OUTPUT_COMMITS].append(commitInfo)

            outputs[OUTPUT_CONTENT].append(content)

        outputs[OUTPUT_RESULT] = True
        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_SUCCESS

    except Exception as e:
        outputs[OUTPUT_ERROR_MESSAGE] = str(e)
        outputs[OUTPUT_STATUS] = OUTPUT_STATUS_FAILURE
        outputs[OUTPUT_RESULT] = False

    return outputs


def validateInputs(inputs, requiredArgs=[]):
    '''
    Validate input arguments
    Parameters
    ----------
    inputs hash : input arguments
    requiredArgs array : list of required arguments
    Raises
    ------
    KeyError if a required argument is not found
    '''
    for requiredArg in requiredArgs:
        if requiredArg not in inputs:
            raise KeyError(f'Input argument {requiredArg} is required')


def setupLogger(logLevel):
    '''
    Setup logger
    Parameters
    ----------
    logLevel str (optional) : Log Level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
    Raises
    ------
    ValueError if logLevel parameter is invalid
    '''
    logger = logging.getLogger()
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    if logLevel is None:
        logLevel = 'INFO'

    numericLoglevel = getattr(logging, logLevel.upper(), None)
    if not isinstance(numericLoglevel, int):
        raise ValueError('Invalid log level: [%s]' % logLevel)

    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] - %(message)s', level=numericLoglevel)
    logging.StreamHandler.emit = lambda self, record: print(logging.StreamHandler.format(self, record))


def setup(inputs):
    setupLogger(inputs.get(INPUT_LOG_LEVEL, None))


def getPagedSlice(page, pageSize, targetItems):
    '''
    Get Paged Slice
    Parameters
    ----------
    page int : the page to retrieve, 0 based
    pageSize int : the number of items per page
    targetItems [] : the source list of items from which to get the page slice
    '''
    start = page * pageSize
    end = min(start + pageSize, len(targetItems))
    if start >= end:
        return []
    else:
        return targetItems[start:end]


def getTokenFromAuthCredentialsLink(context, authCredentialsLink):
    '''
    Retrieve authToken from auth credentials link
    Parameters
    ----------
    context hash : ABX execution context
    authCredentialsLink string : ABX auth credentials URI
    Returns
    -------
    token str : auth token retrieved from the content found at authCredentialsLink
    Raises
    ------
    Exception if there's any error retrieving auth token from auth credentials link
    '''

    try:
        logging.info(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Retrieving token from auth credentials link at [{str(authCredentialsLink)}]...')

        response = context.request(authCredentialsLink, 'GET', '')

        logging.debug(f'[{GITHUB_ENTERPRISE_LOG_PREFIX}] Retrieving token from auth credentials link at' +
                      f' [{str(authCredentialsLink)}] returned [{str(response)}]')

        if response['status'] != 200:
            raise Exception('Failed to obtain auth credentials from '.format(authCredentialsLink))

        return json.loads(response["content"][AUTH_LINK_KEY])

    except Exception as e:
        raise Exception(f'Failed to retrieve credentials from auth credentials link: {str(e)}')
