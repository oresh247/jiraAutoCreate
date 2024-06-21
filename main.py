# coding:utf-8
import json

import docx as docx
import requests
import csv
import configparser
import warnings
import uuid
import pandas as pd
import sqlite3 as sl
import re
import docx
import html
from bs4 import BeautifulSoup


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
sprintId = json.loads(configJira["SPRINT"]["sprintId"])
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
sferaSprintUrl = config["SFERA"]["sferaSprintUrl"]
sferaUrlSearch = config["SFERA"]["sferaUrlSearch"]
sferaUrlKnowledge = config["SFERA"]["sferaUrlKnowledge"]
sferaUrlKnowledge2 = config["SFERA"]["sferaUrlKnowledge2"]
sferaUrlRelations = config["SFERA"]["sferaUrlRelations"]

# session = requests.Session()
# session.auth = (config["USER"]["user"], config["USER"]["password"])
session = requests.Session()
session.post(sferaUrlLogin, json={"username": devUser, "password": devPassword}, verify=False)


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
            "summary": "Устранение дефектов" + " - " + postfixDefectValue[count] + " - " + sprint["name"].split('.')[
                1] + "-" + sprint["name"].split('.')[2],

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
            "summary": epic["fields"]["summary"] + " - " + postfixValue[count] + " - " + sprint["name"].split('.')[
                1] + "-" + sprint["name"].split('.')[2],

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


def changeParent(childId, parentId):
    url = sferaUrl + childId
    data = {"parent": parentId}
    session.patch(url, json=data, verify=False)


def changeSprint(taskId, sprintId):
    url = sferaUrl + taskId
    data = {"sprint": sprintId}
    session.patch(url, json=data, verify=False)


def changeDueDate(taskId, dueDate):
    url = sferaUrl + taskId
    data = {"dueDate": dueDate}
    session.patch(url, json=data, verify=False)


def closeAllDoneSubTask():
    query = "area+%3D+%27SKOKR%27++and+type+in+(%27subtask%27)+and+status+%3D+%27done%27"
    urlQuery = sferaUrl + "?query=" + query
    data = {"status": "closed"}
    response = session.get(urlQuery, verify=False)
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


def testCaseToCVS(testCase, table):
    testIssueCodeValue = testCase['testIssueCode']
    statusValue = testCase['status']
    priorityValue = testCase['priority']
    modifiedByValue = testCase['entityInfo']['modifiedBy']['firstName'] + " " + testCase['entityInfo']['modifiedBy'][
        'lastName']
    linkValue = sferaTestCaseUrl + testIssueCodeValue

    for step in testCase['steps']:
        table['testIssueCode'].append(testIssueCodeValue)
        table['status'].append(statusValue)
        table['priority'].append(priorityValue)
        table['modifiedBy'].append(modifiedByValue)
        table['link'].append(linkValue)
        actionText = step['action']
        actionText = actionText.replace('<br>', '\n')
        actionText = actionText.replace('</p>', '\n')
        actionText = actionText.replace('<li>', '     * ')
        actionText = actionText.replace('</li>', '\n')
        actionText = cleanhtml(actionText)
        table['action'].append(actionText)
        expectedResultText = step['expectedResult']
        expectedResultText = expectedResultText.replace('<br>', '\n')
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
    urlQuery = sferaUrl + "?query=" + query
    response = session.get(urlQuery, verify=False)
    return json.loads(response.text)


def taskSetStatus(taskId, status):
    data = {"status": status}
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)


def taskSetStatusClosed(taskId):
    data = {
        "customFieldsValues": [
            {
                "code": "resolution",
                "value": "Готово"
            }
        ],
        "resolution": [
            "Готово"
        ],
        "status": "closed"
    }
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)


def taskSetSpent(taskId, spent):
    data = \
        {
            "spent": spent,
            "description": "",
            "userLogin": devUser,
            "propertiesToRemove": ["remainder"]
        }
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)


def createTestTable():
    table = {'testIssueCode': [], 'status': [], 'priority': [], 'modifiedBy': [], 'link': [], 'action': [],
             'expectedResult': []}
    sections = getRelisTestCases('151328')
    for testCase in sections['content']:
        testCaseId = testCase['testIssueCode']
        testCase = getTestCase(testCaseId)
        table = testCaseToCVS(testCase, table)

    CVS = pd.DataFrame(table)
    CVS.index = CVS.index + 1
    CVS.to_csv('GFG.csv', encoding="utf-8")
    print(CVS)


def closeAllTaskInSprint(tempCount):
    count = tempCount
    print("Закрыть")
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+hasActiveSprint()+and+type+in+(%27task%27)+and+status%3D%27inProgress%27"
    queryResult = getTaskQuery(query)
    for task in queryResult['content']:
        count = count - 1
        if count == 0:
            return
        taskId = task['number']
        print(taskId)
        # taskSetStatus(taskId, "inProgress")
        # spend = task['estimation']
        # taskSetSpent(taskId, spend)
        taskSetStatusClosed(taskId)

    count = tempCount
    print("В работу")
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
        # taskSetStatus(taskId, "closed")


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
    urlQuery = sferaUrl + "?query=" + query
    data = {"status": "closed"}
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def changeEstimation(sprint, date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and++sprint%3D%27" + sprint + "%27+and+dueDate%3C%22" + date + "%22"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "dueDate": date
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def changeSubTaskSprintDueDate(oldSprint, newSprint, date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+type+in+(%27subtask%27)+and+not+hasOnlyActiveOrPlannedSprint()+and+sprint%3D%27" + oldSprint + "%27"
    #query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and+type+in+(%27subtask%27)+and+sprint%3D%27" + oldSprint + "%27"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "sprint": newSprint,
        "dueDate": date
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def changeNotPlanedDueDate(date):
    query = "statusCategory+!%3D+%27Done%27+and+area+%3D+%27SKOKR%27+and++not+hasOnlyActiveOrPlannedSprint()+and+dueDate%3C%22" + date + "%22"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "dueDate": date
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def changeTypeToSubtask(taskId, parentId, type):
    url = sferaUrl + taskId
    data = {
        "parent": parentId,
        "type": type
    }
    session.patch(url, json=data, verify=False)


def changeDefectSprintDueDate(sprint, newSprint, date):
    query = "sprint%20%3D%20%27" + sprint + "%27%20and%20area%3D%27SKOKR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27defect%27%29"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "dueDate": date,
        "sprint": newSprint
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def createSuperSprintSferaIssue(issuetype):
    with open('tasks.csv', 'r', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)

        for row in reader:
            arrLen = len(row)
            epic = getSferaTask(row[0])
            epicKey = epic["number"]
            print("\n" + "Добавление задач в ЭПИК: " + epicKey)
            workGroup = getWorkGroup(epic)
            archTaskReason = getArchTaskReason(epic)
            deliveryPriority = getDeliveryPriority(epic)

            if issuetype == "Sub-task":
                log[epicKey] = {"workType": workGroup}
            else:
                log[epicKey] = {"workType": workGroup,
                                "epicPriority": deliveryPriority}

            for v in range(1, arrLen):
                totalEstimate = int(row[v])
                sprint = getSferaSprint(sprintId[v - 1])
                sprintName = sprint["name"]
                log[epicKey][sprintName] = {"totalEstimate": totalEstimate}
                print(sprint["name"])
                print("total_estimate_" + str(v - 1) + " = '" + str(totalEstimate) + "'")
                taskCount = 0
                if issuetype == "task":
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
                    if issuetype == "task":
                        task = createSferaTask(epic, curEstimate, sprint, taskCount, workGroup, archTaskReason)
                    elif issuetype == "defect":
                        task = createSferaDefect(epic, curEstimate, sprint, taskCount, workGroup)
                    elif issuetype == "subtask":
                        task = createSubTask(epic, curEstimate, sprint, taskCount)
                    else:
                        task = createSferaTask(epic, curEstimate, sprint, taskCount, workGroup, archTaskReason)
                    taskCount = taskCount + 1
                    taskKey = task.get("number")
                    print("Task created: " + taskKey)
                    log[epicKey][sprintName][taskKey] = {"taskEstimate": curEstimate}

        csv_file.seek(0)
        output = str(log).replace("'", '"')
        return output


def getSferaSprint(sprintId):
    query = '?areaCode=SKOKR&page=0&size=12&statuses=active,planned'
    url = sferaSprintUrl + query
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)

    sprint = json.loads(response.text)
    sprint = [item for item in sprint['content'] if (item['id'] == sprintId)]
    return sprint[0]


def createSferaTask(epic, estimate, sprint, count, workGroup, archTaskReason):
    data = {
        # "name": epic["name"] + " - " + postfixValue[count] + " - " + sprint["name"].split('.')[
        #     1] + "-" + sprint["name"].split('.')[2],
        "name": epic["name"] + " - " + postfixValue[count],
        "assignee": config["SFERAUSER"]["devUser"],
        "owner": config["SFERAUSER"]["devUser"],
        "dueDate": sprint["endDate"],
        "estimation": estimate * 28800,
        "remainder": estimate * 28800,
        "parent": epic["number"],
        "description": epic["description"],
        "priority": "average",
        "status": "created",
        "type": "task",
        "areaCode": jiraProjectKey,
        "sprint": sprint["id"],
        "customFieldsValues": [
            {
                "code": "streamConsumer",
                "value": "Скоринговый конвейер КМБ"
            },
            {
                "code": "streamOwner",
                "value": "Скоринговый конвейер КМБ"
            },
            {
                "code": "projectConsumer",
                "value": "c146f7f3-e894-4f22-bacd-0dcb110b01b4"
            },
            {
                "code": "projectConsumer",
                "value": "da2bc81b-5928-4f05-a7f4-4a9a5e48ce68"
            },
            {
                "code": "projectConsumer",
                "value": "1ec38fc1-2f03-497b-b51e-56e16ad8f260"
            },
            {
                "code": "workGroup",
                "value": workGroup
            },
            {
                "code": "systems",
                "value": "1864 Скоринговый конвейер кредитования малого бизнеса"
            }
        ]
    }

    if archTaskReason != '':
        data['customFieldsValues'].append({
                "code": "archTaskReason",
                "value": archTaskReason
            })

    response = session.post(sferaUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)


def createSferaDefect(epic, estimate, sprint, count, workGroup):
    data = {
        "description": "Устранение дефектов" + " - " + postfixDefectValue[count],
        "assignee": config["SFERAUSER"]["devUser"],
        "owner": config["SFERAUSER"]["devUser"],
        "dueDate": sprint["endDate"],
        "estimation": estimate * 28800,
        "remainder": estimate * 28800,
        # "name": "Устранение дефектов" + " - " + postfixDefectValue[count] + " - " + sprint["name"].split('.')[
        #     1] + "-" + sprint["name"].split('.')[2],
        "name": "Устранение дефектов" + " - " + postfixDefectValue[count],
        "priority": "average",
        "status": "created",
        "type": "defect",
        "areaCode": jiraProjectKey,
        "sprint": sprint["id"],
        "customFieldsValues": [
            {
                "code": "systems",
                # "value": "1854 ОПС ССО"
                "value": "1864 Скоринговый конвейер кредитования малого бизнеса"
            },
            {
                "code": "detectedInSystem",
                # "value": "1854 ОПС ССО"
                "value": "1864 Скоринговый конвейер кредитования малого бизнеса"
            },
            {
                "code": "detectionEnvironment",
                "value": "ИФТ"
            },
            {
                "code": "detectionPhase",
                "value": "СТ"
            },
            {
                "code": "defectType",
                "value": "Функциональный"
            }
        ]
    }

    response = session.post(sferaUrl, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)


def getWorkGroup(epic):
    workGroup = [item for item in epic['customFieldsValues'] if (item['code'] == "workGroup")]
    return workGroup[0]['value']

def getArchTaskReason(epic):
    archTaskReason = [item for item in epic['customFieldsValues'] if (item['code'] == "archTaskReason")]
    if len(archTaskReason) == 0:
        return ''
    else:
        return archTaskReason[0]['value']

def getDeliveryPriority(epic):
    workGroup = [item for item in epic['customFieldsValues'] if (item['code'] == "deliveryPriority")]
    return workGroup[0]['value']


def changeAllNotDoneSubTaskDueDate(date):
    query = "statusCategory%20%21%3D%20%27Done%27%20and%20area%20%3D%20%27SKOKR%27%20and%20type%20in%20%28%27subtask%27%29%20&size=1000&page=0&attributesToReturn=number%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "dueDate": date
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def changeTaskType(epik):
    query = "parent%20%3D%20%27" + epik + "%27%20and%20area%20%3D%20%27SKOKR%27&size=1000&page=0&attributesToReturn=number%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate"
    urlQuery = sferaUrl + "?query=" + query
    data = {
        "customFieldsValues": [
            {
                "code": "archTaskReason",
                "value": "Прочие архитектурные задачи"
            },
            {
                "code": "workGroup",
                "value": "Архитектурная задача"
            }
        ],
        "archTaskReason": [
            "Прочие архитектурные задачи"
        ],
        "workGroup": [
            "Архитектурная задача"
        ]
    }
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)


def getSuperSprintTasks(lst):
    # формируем список спринтов для запроса
    query_sprints = ''
    for sprint in lst:
        query_add = '%2C%27'
        query_end = '%27'
        if query_sprints == '':
            query_add = '%28%27'
        query_sprints += query_add + str(sprint) + query_end
    query_sprints += '%29'
    #query = 'area%3D%27SKOKR%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    query = 'area%3D%27SKOKR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    # SCOR
    #query = 'area%3D%27SCOR%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    #query = 'area%3D%27SCOR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    # SKREQ
    #query = 'area%3D%27SKREQ%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    #query = 'area%3D%27SKREQ%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    # SKSPR
    #query = 'area%3D%27SKSPR%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    #query = 'area%3D%27SKSPR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    # SKPLINT
    #query = 'area%3D%27SKPLINT%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    #query = 'area%3D%27SKPLINT%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    # SCORAFS
    #query = 'area%3D%27SCORAFS%27%20and%20statusCategory%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'
    #query = 'area%3D%27SCORAFS%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20' + query_sprints + '&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cestimation%2Cspent%2Cassignee%2Cowner%2CdueDate%2CupdateDate%2CcreateDate%2CworkGroup'

    urlQuery = sferaUrlSearch + "?query=" + query
    #urlQuery = 'https://sfera.inno.local/app/tasks/api/v0.1/entities?query=area%3D%27SKOKR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27task%27%29%20and%20sprint%20in%20%28%274246%27%2C%274247%27%2C%274248%27%2C%274249%27%2C%274250%27%2C%274251%27%29&size=1000&page=0'
    response = session.get(urlQuery, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)

    tasks = json.loads(response.text)
    return tasks

def checkTasksEstimation(tasks):
    number = []
    name = []
    estimation = []
    sprint = []
    epic = []
    type = []
    for task in tasks['content']:
        number.append(task['number'])
        name.append(task['name'])
        estimation.append(task['estimation'])
        sprint.append(task['actualSprint']['name'])
        type.append(task['workGroup'])
        if 'parentNumber' in task:
            epic.append(task['parentNumber'])
    tasks_df = pd.DataFrame({
        'number': number,
        'name': name,
        'estimation': estimation,
        'sprint': sprint,
        'epic': epic,
        'type': type
    })
    return tasks_df

def changeProject(data, taskId):
    url = sferaUrl + taskId
    session.patch(url, json=data, verify=False)
    print(taskId)


def get_links(story):
    story_data = getSferaTask(story)
    dics = dict()
    for task in story_data['relatedEntities']:
        task_num = task['entity']['number']
        task_name = task['entity']['name']
        dics[task_num] = task_name
    return dics


def search_tasks(page_id,project):
    urlQuery = sferaUrlKnowledge + "cid/" + page_id
    response = session.get(urlQuery, verify=False).json()
    content = response['payload']['content']
    pattern = r'{}{}'.format(project, '-[0-9]{4}')
    matches = re.findall(pattern, content)
    return set(matches)


def add_task_to_story(task_list,story):
    for task in task_list:
        data = {
        "entityNumber": story,
        "relatedEntityNumber": task,
        "relationType": "associatedbugsandstories"
        }
        response = session.post(sferaUrlRelations, json=data, verify=False)
        if response.ok != True:
            raise Exception("Error creating story " + response)


def release_page_gen(parentPage, release, page_name):
    tasks = get_release_tasks(release)
    df = create_release_task_df(tasks)
    grouped_df = create_release_df(df)
    html = generate_release_html(grouped_df)
    publication_release_html(html, parentPage, page_name)


def get_release_tasks(release):
    # Формируем запрос
    query = 'label%20%3D%20%27' + release + '%27&size=1000&page=0&attributesToReturn=checkbox%2Cnumber%2Cname%2CactualSprint%2Cpriority%2Cstatus%2Cassignee%2Cowner%2CdueDate%2Clabel%2CparentNumber%2Ccomponent'
    url = sferaUrl + "?query=" + query
    # Делаем запрос задач по фильтру
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)
    return json.loads(response.text)

def create_release_task_df(tasks):
    # Обрабатываем запрос, проходя по всем задачам и формируя списки
    component_lst = []
    task_directLink_lst = []


    for task in tasks['content']:
        for component in task['component']:
            component_lst.append(component['name'])
            # task_directLink_lst.append(task['directLink'])
            task_number = task['number']
            task_name = task['name']
            template = f"""
    <p><a target=_blank href=https://sfera.inno.local/tasks/task/{task_number} contenteditable=false class=sfera-link sfera-task sfera-link-style style=text-decoration: none; data-rtc-uid=40340632-c702-45bb-a461-93fdd7f681ef rel=noopener data-mce-href=https://sfera.inno.local/tasks/task/{task_number} data-mce-contenteditable=false>{task_number} {task_name}<span>&nbsp;</span>Выполнено<button class=sfera-status-button sfera-status-done>Выполнено</button></a></p>
    """
            task_directLink_lst.append(template)

    tasks_df = pd.DataFrame({
        'Сервис': component_lst,
        'Задачи в сфере': task_directLink_lst

    })
    return tasks_df

def create_release_df(df):
    grouped_df = df.groupby('Сервис').agg(lambda x: ', '.join(map(str, x)))
    grouped_df['Требует выкатку связанный сервис'] = ''
    grouped_df['Версия поставки Новый цод'] = ''
    grouped_df['Версия еДТО'] = ''
    grouped_df['Версия для откатки'] = ''
    grouped_df['Тест-кейсы'] = ''
    grouped_df['БЛОК'] = ''
    grouped_df['Комментарии'] = ''
    return grouped_df


def generate_release_html(grouped_df):
    # Генерируем HTML-код
    html_code = grouped_df.to_html()

    # Декодируем HTML-спецсимволы
    decoded_html = html.unescape(html_code)
    decoded_html = str.replace(decoded_html, '\n', '')
    decoded_html = str.replace(decoded_html, '\\n', '')
    decoded_html = str.replace(decoded_html, '"', '')
    decoded_html = str.replace(decoded_html, 'class=sfera-link sfera-task sfera-link-style',
                               'class="sfera-link sfera-task sfera-link-style"')
    return decoded_html


def publication_release_html(html, parentPage, page_name):
    data = {
        "spaceId": "cbbcfa0b-0542-4407-9e49-61c6aa7caf1b",
        "parentCid": parentPage,
        "name": page_name,
        "content": html
    }
    response = session.post(sferaUrlKnowledge2, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)


# # Генерация страницы ЗНИ
# parent_page = '426943'
# release = 'OKR_20240623_ATM'
# release_page_gen(parent_page, release, release)



# out = createSuperSprintSferaIssue("task")
# out = createSuperSprintSferaIssue("defect")
# print("\n" + out)

# # добавление задач со страницы в Story
# task_list = search_tasks('1258896', 'SKOKR') # Получаем список задач
# add_task_to_story(task_list, 'SKOKR-6107') # Добавляем все задачи в Story

# # Распечатка всех задач в Story
# dics = get_links('SKOKR-6116')
# for key, value in dics.items():
#     print(f"{key}: {value}")


# # Перепривязка проектов
# tasks = getSuperSprintTasks(['4246', '4247', '4248', '4249', '4250', '4251'])
# for task in tasks['content']:
#     number = task['number']
#     parentNumber = task['parentNumber']
#     epic = getSferaTask(parentNumber)
#     projects = [project for project in epic['customFieldsValues'] if project['code'] == "projectConsumer"]
#     new_projects = {'customFieldsValues': projects}
#     changeProject(new_projects, number)
# print(tasks)


# tasks_df = checkTasksEstimation(tasks)
# print (tasks_df)

# changeTaskType("SCOR-2702")
# changeAllNotDoneSubTaskDueDate("2024-07-02")
# changeSubTaskSprintDueDate('4250', '4251', "2024-07-02")
# changeDefectSprintDueDate('21', '22', "2023-09-26")
# changeTypeToSubtask("SKOKR-4828", "SKOKR-4625", "subtask")
# changeNotPlanedDueDate("2023-09-27")
# changeEstimation('19', "2023-08-15")
# closeAllDoneTask()
closeAllTaskInSprint(6)
# closeAllDefectInSprint()
# changeChildParent("SKOKR-4625", "SKOKR-4629")
# changeChildParent("SKOKR-4625", "SKOKR-4625")
# changeSprint("SKOKR-4318",18)
# changeDueDate("SKOKR-4318","2023-08-01")
# closeAllDoneSubTask()
# out = createSuperSprintIssue("Sub-task")
# out = createSuperSprintIssue("Task")
# out = createSuperSprintIssue("Defect")
# print("\n" + out)


