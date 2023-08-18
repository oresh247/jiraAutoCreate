# coding:utf-8
import json
import requests
import csv
import configparser
import warnings
import uuid
import pandas as pd
import re

from requests.auth import HTTPBasicAuth

warnings.filterwarnings("ignore")

config = configparser.ConfigParser()
configJira = configparser.ConfigParser()
config.read("config.ini", encoding='utf-8')
configJira.read("configFields.ini", encoding='utf-8')

streamKey = config["JIRA"]["streamKey"]
systemKey = config["JIRA"]["systemKey"]
projectKey = config["JIRA"]["projectKey"]
jiraProjectKey = config["JIRA"]["jiraProjectKey"]
jiraUrl = config["JIRA"]["jiraUrl"]
sprintUrl = config["JIRA"]["sprintUrl"]
jiraSprintsId = json.loads(configJira["SPRINT"]["sprintId"])
postfixValue = json.loads(configJira["POSTFIX"]["postfixValue"])
postfixDefectValue = json.loads(configJira["POSTFIX"]["postfixDefectValue"])
log = {}
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

# СФЕРА параметры
devUser = config["SFERAUSER"]["devUser"]
devPassword = config["SFERAUSER"]["devPassword"]
sferaUrl = config["SFERA"]["sferaUrl"]
sferaUrlLogin = config["SFERA"]["sferaUrlLogin"]
sferaTestCaseUrl = config["SFERA"]["sferaTestCaseUrl"]
sferaTSectionsUrl = config["SFERA"]["sferaTSectionsUrl"]


#session = requests.Session()
#session.auth = (config["USER"]["user"], config["USER"]["password"])
session = requests.Session()
session.post(sferaUrlLogin, json={"username": devUser,"password": devPassword}, verify=False)


def createStory(summary, description, acceptanceCriteria, labels):
    data = {
        "fields": {
            "project": {
                "key": jiraProjectKey
            },
            "summary": summary,
            "description": description,
            "labels": labels,
            "issuetype": {
                "name": "Story"
            },
            "timetracking": {
                "originalEstimate": "1m",
                "remainingEstimate": "1m"
            },
            "customfield_11609": acceptanceCriteria,
            "customfield_17501": {"id": "16000"},
            "customfield_16202": [
                {"key": projectKey}
            ],
            "customfield_16201": [
                {"key": systemKey}
            ],
            "customfield_16206": [
                {"key": streamKey}
            ]
        }
    }
    response = session.post(jiraUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story")
    return json.loads(response.text)

def createDefect(epic, estimate, sprint, count):
    data = {
        "fields": {
            # Проект-заказчик_new:
            "project": {
                "key": jiraProjectKey
            },

            # Название:
            "summary": "Устранение дефектов" + " - " + postfixDefectValue[count] + " - " + sprint["name"].split('.')[1] + "-" + sprint["name"].split('.')[2],

            "issuetype": {
                "name": "Defect"
            },

            # Учет времени:
            "timetracking": {
                "originalEstimate": str(estimate) + "d",
                "remainingEstimate": str(estimate) + "d"
            },

            # Системы обнаружения::
            "customfield_139999100": [
                {"key": systemKey}
            ],

            # Story Points:
            "customfield_10200": estimate,

            # Epic Link:
            "customfield_10101": epic["key"],

            # Sprint:
            "customfield_10100": sprint["id"],

            # Срок исполнения:
            "duedate": sprint["endDate"],

            # Среда обнаружения:
            "customfield_11805": {"value": "DEV"},

            # Фаза обнаружения:
            "customfield_11806": {"value": "СТ"},

            # Претензионная работа:
            "customfield_15900": {"value": "Нет"},

            # Исполнитель:
            "assignee": {"name": config["USER"]["user"]}

        }
    }

    response = session.post(jiraUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)

# def createTask(summary, parentKey, labels):
def createTask(epic, estimate, sprint, count):
    data = {
        "fields": {
            # Проект-заказчик_new:
            "project": {
                "key": jiraProjectKey
            },
            # Название:
            "summary": epic["fields"]["summary"] + " - " + postfixValue[count] + " - " + sprint["name"].split('.')[1] + "-" + sprint["name"].split('.')[2],

            "issuetype": {
                "name": "Task"
            },
            # Учет времени:
            "timetracking": {
                "originalEstimate": str(estimate) + "d",
                "remainingEstimate": str(estimate) + "d"
            },
            # Системы_new:
            "customfield_16201": [
                {"key": systemKey}
            ],
            # Проект-заказчик_new:
            "customfield_15715": [
                {"key": projectKey}
            ],
            # Стрим-заказчик_new:
            "customfield_16205": [
                {"key": streamKey}
            ],

            # Стрим-владелец_new:
            "customfield_16206": [
                {"key": streamKey}
            ],
            # Тип работ:
            "customfield_11600": epic["fields"]["customfield_11600"],

            # Причины арх.задачи:
            "customfield_17900": epic["fields"]["customfield_17900"],

            # Причины Тех.долга:
            "customfield_12917": epic["fields"]["customfield_12917"],

            # Класс причины:
            "customfield_17901": epic["fields"]["customfield_17901"],

            # Story Points:
            "customfield_10200": estimate,

            # Epic Link:
            "customfield_10101": epic["key"],

            # Sprint:
            "customfield_10100": sprint["id"],

            # Срок исполнения:
            "duedate": sprint["endDate"],

            # Исполнитель:
            "assignee": {"name": config["USER"]["user"]}

        }
        # "update": {
        #     "issuelinks": [
        #         {
        #             "add": {
        #                 "type": {"name": "Child"},
        #                 "outwardIssue": {"key": parentKey}
        #             }
        #         }
        #     ]
        # }
    }
    response = session.post(jiraUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)

def createSubTask(epic, estimate, sprint, count):
    data = {
        "fields": {
            # Проект-заказчик_new:
            "project": {
                "key": jiraProjectKey
            },
            # Родительская задача:
            "parent": {
                "key": epic["key"]
            },
            # Название:
            "summary": epic["fields"]["summary"],

            "issuetype": {
                "name": "Sub-task"
            },
            # Учет времени:
            "timetracking": {
                "originalEstimate": str(estimate) + "d",
                "remainingEstimate": str(estimate) + "d"
            },
            # Вид работ:
            "customfield_11601": {"value": "СТ/РТ"},

            # # Системы_new:
            # "customfield_16201": [
            #     {"key": systemKey}
            # ],
            # # Проект-заказчик_new:
            # "customfield_15715": [
            #     {"key": projectKey}
            # ],
            # # Стрим-заказчик_new:
            # "customfield_16205": [
            #     {"key": streamKey}
            # ],
            #
            # # Стрим-владелец_new:
            # "customfield_16206": [
            #     {"key": streamKey}
            # ],
            # # Тип работ:
            # "customfield_11600": epic["fields"]["customfield_11600"],
            #
            # # Причины арх.задачи:
            # "customfield_17900": epic["fields"]["customfield_17900"],
            #
            # # Причины Тех.долга:
            # "customfield_12917": epic["fields"]["customfield_12917"],
            #
            # # Класс причины:
            # "customfield_17901": epic["fields"]["customfield_17901"],

            # Story Points:
            "customfield_10200": estimate,

            # # Epic Link:
            # "customfield_10101": epic["key"],
            #
            # # Sprint:
            # "customfield_10100": sprint["id"],

            # Срок исполнения:
            "duedate": sprint["endDate"],

            # Исполнитель:
            "assignee": {"name": config["USER"]["user"]}

        }
        # "update": {
        #     "issuelinks": [
        #         {
        #             "add": {
        #                 "type": {"name": "Child"},
        #                 "outwardIssue": {"key": parentKey}
        #             }
        #         }
        #     ]
        # }
    }

    response = session.post(jiraUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)

def createAllIssues(issueSummary, issueDescription, issueAcceptanceCriteria, issueLabels):
    # print("Creating new issue (" + issueSummary + ":" + issueDescription + "")
    # story = createStory(issueSummary, issueDescription, issueAcceptanceCriteria, issueLabels)
    # print("Story created: " + story.get("key"))
    task = createTask("FE. " + issueSummary, issueLabels)
    print("Task created: " + task.get("key"))
    # task = createTask("BE. " + issueSummary, story.get("key"), issueLabels)
    # print("Task created: " + task.get("key"))
    # task = createTask("QA.CASE " + issueSummary, story.get("key"), issueLabels)
    # print("Task created: " + task.get("key"))
    # task = createTask("QA.TEST " + issueSummary, story.get("key"), issueLabels)
    # print("Task created: " + task.get("key"))

def getIssue(issueKey):
    url = jiraUrl + issueKey
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get issue data " + response)
    return json.loads(response.text)

def getSprint(sprintId):
    url = sprintUrl + str(sprintId)
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)
    return json.loads(response.text)

def createSuperSprintIssue(issuetype):
    with open('tasks.csv', 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)

        for row in reader:
            arrLen = len(row)
            epic = getIssue(row[0])
            epicKey = epic["key"]
            print("\n" + "Добавление задач в ЭПИК: " + epicKey)

            if issuetype == "Sub-task":
                log[epicKey] = {"workType": epic["fields"]["customfield_11600"]["value"]}
            else:
                log[epicKey] = {"workType": epic["fields"]["customfield_11600"]["value"],
                                "epicPriority": epic["fields"]["customfield_13916"]["value"]}

            for v in range(1, arrLen):
                totalEstimate = int(row[v])
                sprint = getSprint(jiraSprintsId[v - 1])
                sprintName = sprint["name"]
                log[epicKey][sprintName] = {"totalEstimate": totalEstimate}
                print(sprint["name"])
                print("total_estimate_" + str(v - 1) + " = '" + str(totalEstimate) + "'")
                taskCount = 0
                if issuetype == "Task":
                    maxIssueEstimate = 3
                else:
                    maxIssueEstimate = 3

                while totalEstimate > 0:
                    if totalEstimate >= maxIssueEstimate:
                        curEstimate = maxIssueEstimate
                        totalEstimate = totalEstimate - maxIssueEstimate
                    else:
                        curEstimate = totalEstimate
                        totalEstimate = 0
                    print("new_issue_estimate = " + str(curEstimate))
                    if issuetype == "Task":
                        task = createTask(epic, curEstimate, sprint, taskCount)
                    elif issuetype == "Defect":
                        task = createDefect(epic, curEstimate, sprint, taskCount)
                    elif issuetype == "Sub-task":
                        task = createSubTask(epic, curEstimate, sprint, taskCount)
                    else:
                        task = createTask(epic, curEstimate, sprint, taskCount)
                    taskCount = taskCount + 1
                    taskKey = task.get("key")
                    print("Task created: " + taskKey)
                    log[epicKey][sprintName][taskKey] = {"taskEstimate": curEstimate}

        csv_file.seek(0)
        output = str(log).replace("'", '"')
        return output

def getSferaTask(taskId):
    url = sferaUrl + taskId
    response = session.get(url, verify=False)
    return json.loads(response.text)

def changeChildParent(oldParentId, newParentId):
    task = getSferaTask(oldParentId)
    for childTask in task['childEntities']:
        if childTask['status'] != 'closed':
            print(childTask['number'])
            changeParent(childTask['number'], newParentId)

def changeParent(childId,parentId):
    url = sferaUrl + childId
    data = {"parent": parentId}
    session.patch(url, json=data, verify=False)

def changeSprint(taskId,sprintId):
    url = sferaUrl + taskId
    data = {"sprint": sprintId}
    session.patch(url, json=data, verify=False)

def changeDueDate(taskId,dueDate):
    url = sferaUrl + taskId
    data = {"dueDate":dueDate}
    session.patch(url, json=data, verify=False)

def closeAllDoneSubTask():
    query = "area+%3D+%27SKOKR%27++and+type+in+(%27subtask%27)+and+status+%3D+%27done%27"
    urlQuery = sferaUrl+ "?query=" + query
    data = {"status": "closed"}
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)

def getTestCase(testCaseId):
    url = sferaTestCaseUrl + testCaseId
    response = session.get(url, verify=False)
    return json.loads(response.text)

def testCaseToCVS(testCase,table):
    testIssueCodeValue=testCase['testIssueCode']
    statusValue=testCase['status']
    priorityValue=testCase['priority']
    modifiedByValue=testCase['entityInfo']['modifiedBy']['firstName']+" "+testCase['entityInfo']['modifiedBy']['lastName']
    linkValue=sferaTestCaseUrl + testIssueCodeValue

    for step in testCase['steps']:
        table['testIssueCode'].append(testIssueCodeValue)
        table['status'].append(statusValue)
        table['priority'].append(priorityValue)
        table['modifiedBy'].append(modifiedByValue)
        table['link'].append(linkValue)
        actionText = step['action']
        actionText = actionText.replace('<br>','\n')
        actionText = actionText.replace('</p>', '\n')
        actionText = actionText.replace('<li>', '     * ')
        actionText = actionText.replace('</li>', '\n')
        actionText = cleanhtml(actionText)
        table['action'].append(actionText)
        expectedResultText = step['expectedResult']
        expectedResultText = expectedResultText.replace('<br>','\n')
        expectedResultText = expectedResultText.replace('</p>', '\n')
        expectedResultText = expectedResultText.replace('<li>', '     * ')
        expectedResultText = expectedResultText.replace('</li>', '\n')
        expectedResultText = cleanhtml(expectedResultText)
        table['expectedResult'].append(expectedResultText)
    return table

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def getRelisTestCases(sections):
    url = sferaTSectionsUrl + sections + '/test-issues'
    response = session.get(url, verify=False)
    return json.loads(response.text)

def getTaskQuery(query):
    urlQuery = sferaUrl+ "?query=" + query
    response=session.get(urlQuery, verify=False)
    return json.loads(response.text)

def taskSetStatus(taskId,status):
    data = {"status": status}
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)

def taskSetSpent(taskId,spent):
    data = \
        {
            "spent": spent,
            "propertiesToRemove": ["remainder"]
        }
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)

def createTestTable():
    table = {'testIssueCode': [],'status': [],'priority': [],'modifiedBy': [],'link': [],'action': [], 'expectedResult': []}
    sections = getRelisTestCases('151328')
    for testCase in sections['content']:
        testCaseId = testCase['testIssueCode']
        testCase = getTestCase(testCaseId)
        table = testCaseToCVS(testCase, table)

    CVS = pd.DataFrame(table)
    CVS.index = CVS.index + 1
    CVS.to_csv('GFG.csv', encoding="utf-8")
    print(CVS)

def closeAllTaskInSprint(count):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+hasActiveSprint()+and+type+in+(%27task%27)+and+status%3D%27created%27"
    queryResult = getTaskQuery(query)
    for task in queryResult['content']:
        count = count - 1
        if count == 0:
            return
        taskId = task['number']
        print(taskId)
        taskSetStatus(taskId, "inProgress")
        spend = task['estimation']
        taskSetSpent(taskId, spend)
        taskSetStatus(taskId, "closed")

def closeAllDefectInSprint():
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+hasActiveSprint()+and+type+in+(%27defect%27)+and+status%3D%27created%27"
    queryResult = getTaskQuery(query)
    for task in queryResult['content']:
        taskId = task['number']
        taskSetStatus(taskId, "analysis")
        taskSetStatus(taskId, "fixing")
        spend = task['estimation']
        taskSetSpent(taskId, spend)
        taskSetStatus(taskId, "testing")
        taskSetStatus(taskId, "closed")

def closeAllDoneTask():
    query = "area+%3D+%27SKOKR%27++and+type+in+(%27task%27)+and+hasActiveSprint()++and+status+%3D+%27done%27"
    urlQuery = sferaUrl+ "?query=" + query
    data = {"status": "closed"}
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)

def changeEstimation(sprint,date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and++sprint%3D%27"+sprint+"%27+and+dueDate%3C%22"+date+"%22"
    urlQuery = sferaUrl+ "?query=" + query
    data = {
        "dueDate": date
    }
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)

def changeSubTaskSprintDueDate(oldSprint,newSprint,date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+type+in+(%27subtask%27)+and+not+hasOnlyActiveOrPlannedSprint()+and+sprint%3D%27"+oldSprint+"%27"
    urlQuery = sferaUrl+ "?query=" + query
    data = {
        "sprint": newSprint,
        "dueDate": date
    }
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)

def changeNotPlanedDueDate(date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and++not+hasOnlyActiveOrPlannedSprint()+and+dueDate%3C%22"+date+"%22"
    urlQuery = sferaUrl+ "?query=" + query
    data = {
        "dueDate": date
    }
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)

def changeTypeToSubtask(taskId,parentId,type):
    url = sferaUrl + taskId
    data = {
        "parent": parentId,
        "type": type
    }
    session.patch(url, json=data, verify=False)

def changeDefectSprintDueDate(sprint, newSprint, date):
    query = "sprint%20%3D%20%27" + sprint + "%27%20and%20area%3D%27SKOKR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27defect%27%29"
    urlQuery = sferaUrl+ "?query=" + query
    data = {
        "dueDate": date,
        "sprint": newSprint
    }
    response=session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


#changeSubTaskSprintDueDate('19', '20', "2023-08-22")
#changeDefectSprintDueDate('19', '20', "2023-08-22")
#changeTypeToSubtask("SKOKR-4828", "SKOKR-4625", "subtask")
#changeNotPlanedDueDate("2023-09-27")
#changeEstimation('19', "2023-08-15")
#closeAllDoneTask()
closeAllTaskInSprint(5)
#closeAllDefectInSprint()
#changeChildParent("SKOKR-4625", "SKOKR-4629")
#changeChildParent("SKOKR-4625", "SKOKR-4625")
#changeSprint("SKOKR-4318",18)
#changeDueDate("SKOKR-4318","2023-08-01")
#closeAllDoneSubTask()
#out = createSuperSprintIssue("Sub-task")
#out = createSuperSprintIssue("Task")
#out = createSuperSprintIssue("Defect")
#print("\n" + out)




