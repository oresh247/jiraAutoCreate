# coding:utf-8
import json
import requests
import csv
import configparser
import warnings

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

session = requests.Session()
session.auth = (config["USER"]["user"], config["USER"]["password"])


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
            "summary": "Устранение дефектов Q1" + " - " + postfixDefectValue[count] + " - " + sprint["name"].split('.')[1] + "-" + sprint["name"].split('.')[2],

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


out = createSuperSprintIssue("Sub-task")
#out = createSuperSprintIssue("Task")
#out = createSuperSprintIssue("Defect")

print("\n" + out)

