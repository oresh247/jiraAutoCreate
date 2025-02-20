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
import pandas as pd
import numpy as np
import os

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
checkDescription = json.loads(configJira["CHECK"]["checkDescription"])
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
sferaUrlViews = config["SFERA"]["sferaUrlViews"]

# Сервисы
OKR_SERVICE_LST = json.loads(configJira["SERVICE"]["OKR_SERVICE_LST"])

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
    urlQuery = sferaUrlSearch + "?query=" + query
    data = {"status": "closed"}
    response = session.get(urlQuery, verify=False)
    subTasks = json.loads(response.text)
    for subTask in subTasks['content']:
        subTaskNumber = subTask['number']
        print(subTaskNumber)
        url = sferaUrl + subTaskNumber
        session.patch(url, json=data, verify=False)
def getSferaTask(taskId):
    url = sferaUrl + taskId
    response = session.get(url, verify=False)
    return json.loads(response.text)

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
    urlQuery = sferaUrlSearch + "?query=" + query
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
    urlQuery = sferaUrlSearch + "?query=" + query
    #urlQuery = sferaUrl + "?query=" + query
    #urlQuery = "https://sfera.inno.local/app/tasks/api/v1/entity-views?page=0&size=20&attributes=checkbox%2Cnumber%2Cname%2Cpriority%2Cstatus%2Cassignee%2Cowner%2CdueDate%2Clabel%2Ccomponent%2CactualSprint%2Cdecision%2Cresolution%2CnameProject%2CarchTaskReason%2CexternalLinks%2Cattachments%2Csystems%2CsubSystems%2CstreamConsumer%2CstreamOwner%2CprojectConsumer%2CaffectedInVersion%2CfixedInVersion%2C%20rank%2C%20id%2C%20parent%2C%20worklog%2C%20type%2C%20serviceClass%2C%20estimation&query=area%3D%27SKOKR%27%20and%20statusCategory%21%3D%27Done%27%20and%20type%20in%20%28%27subtask%27%29%20and%20sprint%20%3D%20%274259%27"
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
    urlQuery = sferaUrlSearch + "?query=" + query
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
        "assignee": config["SFERAUSER"]["assignee"],
        "owner": config["SFERAUSER"]["assignee"],
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
                "code": "workGroup",
                "value": workGroup
            }
        ]
    }

    if archTaskReason != '':
        data['customFieldsValues'].append({
                "code": "archTaskReason",
                "value": archTaskReason
            })

    projects = [project for project in epic['customFieldsValues'] if project['code'] == "projectConsumer"]

    if len(projects) != 0:
        for project in projects:
            data['customFieldsValues'].append({
                "code": project['code'],
                "value": project['value']
            })

    systems = [system for system in epic['customFieldsValues'] if system['code'] == "systems"]

    if len(systems) != 0:
        for system in systems:
            data['customFieldsValues'].append({
                "code": system['code'],
                "value": system['value']
            })
    else:
        data['customFieldsValues'].append({
            "code": "systems",
            # "value": "1854 ОПС ССО"
            "value": "1864 Скоринговый конвейер кредитования малого бизнеса"
        })

    laborActivitys = [laborActivity for laborActivity in epic['customFieldsValues'] if laborActivity['code'] == "laborActivity"]
    if len(laborActivitys) != 0:
        for laborActivity in laborActivitys:
            data['customFieldsValues'].append({
                "code": laborActivity['code'],
                "value": laborActivity['value']
            })

    specLimits = [specLimit for specLimit in epic['customFieldsValues'] if specLimit['code'] == "specLimit"]
    if len(specLimits) != 0:
        for specLimit in specLimits:
            data['customFieldsValues'].append({
                "code": specLimit['code'],
                "value": specLimit['value']
            })

    response = session.post(sferaUrlSearch, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)


def createSferaDefect(epic, estimate, sprint, count, workGroup):
    data = {
        "description": "Устранение дефектов" + " - " + postfixDefectValue[count],
        "assignee": config["SFERAUSER"]["assignee"],
        "owner": config["SFERAUSER"]["assignee"],
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
                #"value": "1854 ОПС ССО"
                "value": "1864 Скоринговый конвейер кредитования малого бизнеса"
            },
            {
                "code": "detectedInSystem",
                #"value": "1854 ОПС ССО"
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

    response = session.post(sferaUrlSearch, json=data, verify=False)
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
    urlQuery = sferaUrlSearch + "?query=" + query
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
        if task['relationType'] != 'clones' and task['relationType'] != 'isClonedBy':
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


def get_epics_for_check():
    # Формируем запрос
    #"https://sfera.inno.local/app/tasks/api/v1/entity-views?page=0&size=20&attributes=checkbox%2Cnumber%2Cname%2Cstatus%2Cassignee%2Cowner%2CdueDate%2Clabel%2Ccomponent%2CactualSprint%2Cestimation%2CacceptanceCriteria%2Cdescription%2CworkGroup%2Csystems%2CtargetSuperSprint%2CdeliveryPriority%2CstreamConsumer%2CstreamOwner%2Cresolution%2CarchTaskReason%2CexternalLinks%2Cattachments%2CsubSystems%2CprojectConsumer%2CaffectedInVersion%2CfixedInVersion%2C%20rank%2C%20id%2C%20parent%2C%20worklog%2C%20type%2C%20serviceClass%2C%20estimation&query=area%20%3D%20%27SCOR%27%20and%20type%20%3D%20%27epic%27%20and%20targetSuperSprint%20%3D%20%27%D0%A1%D0%A12025.1%27"
    page_size = "?page=0&size=200"
    attributes = "&attributes=checkbox%2Cnumber%2Cname%2Cstatus%2Cassignee%2Cowner%2CdueDate%2Clabel%2Ccomponent%2CactualSprint%2Cestimation%2CacceptanceCriteria%2Cdescription%2CworkGroup%2Csystems%2CtargetSuperSprint%2CdeliveryPriority%2CstreamConsumer%2CstreamOwner%2Cresolution%2CarchTaskReason%2CexternalLinks%2Cattachments%2CsubSystems%2CprojectConsumer%2CaffectedInVersion%2CfixedInVersion%2C%20rank%2C%20id%2C%20parent%2C%20worklog%2C%20type%2C%20serviceClass%2C%20estimation"
    query = "&query=area%20%3D%20%27SCOR%27%20and%20type%20%3D%20%27epic%27%20and%20targetSuperSprint%20%3D%20%27%D0%A1%D0%A12025.1%27"
    url = sferaUrlViews + page_size + attributes + query
    # Делаем запрос задач по фильтру
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)
    return json.loads(response.text)


def epic_check_description(epics):
    epic_list = []
    for epic in epics['content']:
        attr_list = []
        number = epic['number']
        name = epic['name']

        if "deliveryPriority" in epic:
            deliveryPriority = epic['deliveryPriority']["name"]
        else:
            deliveryPriority = "не назначен"

        acceptanceCriteria = epic['acceptanceCriteria']

        if "owner" in epic:
            owner = epic['owner']["name"]
        else:
            owner = "не назначен"

        if "assignee" in epic:
            assignee = epic['assignee']["name"]
        else:
            assignee = "не назначен"

        attr_list.append(number)
        attr_list.append(deliveryPriority)

        attr_list.append(name)
        attr_list.append(assignee)

        attr_list.append(owner)
        attr_list.append(acceptanceCriteria)
        if 'description' in epic:
            desc = epic['description'].lower()
        else:
            desc = ""
        desc_len = len(desc)
        attr_list.append(desc_len)
        for check in checkDescription:
            if check in desc:
                result = 1
            else:
                result = 0
            attr_list.append(result)
        epic_list.append(attr_list)

    columns = ["ЭПИК", "Приоритет", "Заголовок", "Исполнитель", "Владелец", "Критерий приемки", "описание (символов)"] + checkDescription
    df = pd.DataFrame(epic_list, columns=columns)
    return df


def generate_release_html(tasks_df):
    # Генерируем HTML-код
    html_code = tasks_df.to_html(index=False)

    # Декодируем HTML-спецсимволы
    decoded_html = html.unescape(html_code)
    decoded_html = str.replace(decoded_html, '\n', '')
    decoded_html = str.replace(decoded_html, '\\n', '')
    decoded_html = str.replace(decoded_html, '"', '')
    decoded_html = str.replace(decoded_html, "'", '"')
    decoded_html = str.replace(decoded_html, 'class=sfera-link sfera-task sfera-link-style',
                               'class="sfera-link sfera-task sfera-link-style"')
    decoded_html = str.replace(decoded_html, '<table border=1 class=dataframe>',
                               '<table class="MsoNormalTable" border="1" cellspacing="0" cellpadding="0" width="1440" data-widthmode="wide" data-lastwidth="1761px" style="border-collapse: collapse; width: 1761px;" data-rtc-uid="67d29bf0-31c7-4de5-909d-8cea7a11f75f" id="mce_2">')
    return decoded_html


def replace_release_html(html, page_id):
    url1 = sferaUrlKnowledge + 'cid/' + page_id
    response = session.get(url1, verify=False)
    id = json.loads(response.text)['payload']['id']
    data = {
        "id": id,
        "content": html,
        "name": "Проверка ЭПИКов"
    }
    url2 =sferaUrlKnowledge2 + '/' + page_id
    response = session.patch(url2, json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)

def check_epics(page_id):
    # Получить список эпиков
    epics = get_epics_for_check()


    # # Сохраняем данные в файл
    # with open('epics.json', 'w', encoding='utf-8') as file:
    #     json.dump(epics, file, ensure_ascii=False, indent=4)

    # # Открываем файл data.json в режиме чтения
    # with open('epics.json', 'r', encoding='utf-8') as file:
    #     # Загружаем данные из файла в переменную data
    #     epics = json.load(file)


    # Выполнить проверки по эпикам
    df = epic_check_description(epics)
    html = generate_release_html(df)
    replace_release_html(html, page_id)

    # Опубликовать отчет
    print(df)


def get_sprints():
    url = "https://sfera.inno.local/app/tasks/api/v0.1/sprints?areaCode=SCOR&page=0&size=150&statuses=active,planned"
    # Делаем запрос задач по фильтру
    response = session.get(url, verify=False)
    if response.ok != True:
        raise Exception("Error get sprint data " + response)
    sprints = json.loads(response.text)
    # Сохраняем данные в файл
    with open('sprints.json', 'w', encoding='utf-8') as file:
        json.dump(sprints, file, ensure_ascii=False, indent=4)
    return sprints


def getServiceId(serviceName):
    response = session.get("https://sfera.inno.local/app/tasks/api/v1/components?keyword=s&page=0&size=100&areaCode=SKOKR&sort=name", verify=False)
    if response.ok != True:
        print("Error get id service" + serviceName)

    # Преобразуем строку JSON в словарь
    data = json.loads(response.text)

    # Ищем сервис по имени
    for service in data['content']:
        if service['name'] == serviceName:
            return service['id']


def createSubtaskFromTask(serviceName, taskId, taskName, taskDescription):
    serviceId = getServiceId(serviceName)
    data = {
        "name": "[" + serviceName + "] " + taskName,
        "priority": "average",
        "status": "created",
        "area": "SKOKR",
        "type": "subtask",
        "description": taskDescription,
        "assignee": "vtb4068421@corp.dev.vtb",
        "owner": "vtb4068421@corp.dev.vtb",
        "label": [
            {
                "id": 59055
            }
        ],
        "component": [
            {
                "id": serviceId
            }
        ],
        "parent": taskId,
        "workType": "Разработка",
        "rightTransferApproval": True
    }

    #response = session.post(sferaUrlSearch, json=data, verify=False)
    response = session.post("https://sfera.inno.local/app/tasks/api/v1/entities", json=data, verify=False)
    if response.ok != True:
        raise Exception("Error creating story " + response)
    return json.loads(response.text)


def createSubtaskForAllServices(taskId):
    subtaskLst = []
    task = getSferaTask(taskId)
    taskName = task['name']
    taskDescription = task['description']
    for serviceName in OKR_SERVICE_LST:
        subtask = createSubtaskFromTask(serviceName, taskId, taskName, taskDescription)
        subtaskLst.append(subtask['number'])
    return subtaskLst


# # Создание подзадач на все сервисы ОКР
# taskId = "SKOKR-7020"
# taskList = createSubtaskForAllServices(taskId)
# print(taskList)

# Получение списка ЭПИКов и сохранение в JSON
# epics = get_sprints()


# Проверка Эпиков
# check_epics("1422085")


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

# Распечатка всех задач в Story
# story = 'SKOKR-7100'
# dics = get_links(story)
# print('STORY: ' + story)
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
# changeAllNotDoneSubTaskDueDate("2024-12-18")
# changeSubTaskSprintDueDate('4333', '4334', "2025-02-26")
# changeDefectSprintDueDate('21', '22', "2023-09-26")
# changeTypeToSubtask("SKOKR-4828", "SKOKR-4625", "subtask")
# changeNotPlanedDueDate("2024-09-24")
# changeEstimation('19', "2023-08-15")
# closeAllDoneTask()
# closeAllTaskInSprint(6)
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

# data = pd.read_csv('area.csv', index_col=0)
# print(data.loc['SKOKR']['email'])




