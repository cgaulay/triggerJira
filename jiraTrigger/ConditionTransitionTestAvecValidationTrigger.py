#Jython condition script for JIRA trigger
from com.atlassian.jira import ComponentManager
from com.atlassian.jira.issue import CustomFieldManager
projects = ['front', 'orchestrateur', 'worc', 'api']
cfm = ComponentManager.getInstance().getCustomFieldManager()
jac = ComponentManager.getInstance().getJiraAuthenticationContext()
userUtil = ComponentManager.getInstance().getUserUtil()
currentUser = jac.getLoggedInUser()
provenance = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("Provenance"))
byPassGroup = "CT.RMFixe.pilotage"
criticite = issue.getPriorityObject().getName()
project_id = ''
#project_id = 'front-pj-fd'
issueType = issue.getIssueTypeObject().getName()
#getProjectName
def getProjectName():
    global description
    global project_id
    global result
    projetPolarion = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("Projet(s) Polarion"))
    if repr(projetPolarion) != 'None':
        if len(projetPolarion) > 1:
                log.error('[' + defect_id + '] ' + E7)
                description = u'ERREUR : Le champ "Projet(s) Polarion" ne doit contenir qu\'un seul projet : ' + str(projetPolarion)
                result = False
                sendMetrics(E7)
        else:
            project_id = str(projetPolarion[0])
            project_id = project_id.replace("_", "-")
            result = True
    else:
        project_id = issue.getProjectObject().getName()
        result = True
    return project_id
def checkProjectType(P_project_name):
    ptype = P_project_name.split('-')
    if ptype[0] in projects:
        return True

def checkCurrentUserGroup(P_currentUserId):
    userGroups = userUtil.getGroupNamesForUser(currentUser.getName())
    print userGroups
    if (byPassGroup) in userGroups:
        return True
    else:
        return False
project_id = getProjectName()
if repr(provenance) =='None' and (criticite == 'Bloquant' or criticite == 'Majeur') and checkProjectType(project_id) and issueType == "Anomalie" and not checkCurrentUserGroup(currentUser):
    result = True
else:
    result = False