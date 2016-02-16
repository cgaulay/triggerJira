#Jython post function script for send metrics
from com.atlassian.jira import ComponentManager
from com.atlassian.jira.issue import CustomFieldManager
from com.xhaus.jyson import JysonCodec as json
import httplib
import datetime
cfm = ComponentManager.getInstance().getCustomFieldManager()
provenance = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("Provenance"))
criticite = issue.getPriorityObject().getName()
project_id = issue.getProjectObject().getName()
dateCreationJira = issue.getCreated().toString()

def sendMetrics(P_error):
    now = datetime.datetime.today()
    defect_id = issue.getKey()
    JiraCreationDate = datetime.datetime.strptime(dateCreationJira, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S') + '+01:00'

    params = {}
    params["criticality"] = criticite
    params["date"] = now.strftime('%Y-%m-%dT%H:%M') + '+01:00'
    params["defect_id"] = defect_id
    params["defect_project"] = str(project_id)
    params["error_message"] = P_error
    params["type"] = str(provenance)
    params["status"] = 1
    params["date_created_jira"] = JiraCreationDate
    params = json.dumps(params)

    headers = {}
    headers['Content-Type'] = "application/json"
    headers['Accept'] = "application/json"

    try:
        conn = httplib.HTTPConnection('cd.pagesjaunes.fr')
        conn.request('PUT', '/dashboard-cd/api/measure/defect', params, headers)
        response = conn.getresponse()
        log.info('Envoi des indicateurs bypass Trigger : ' + response.reason)
    except:
        log.warn('Impossible d\'envoyer les métriques')
        pass

if repr(provenance) !='None' and (criticite == 'Bloquant' or criticite == 'Majeur') and issueType == "Anomalie":
    sendMetrics("")