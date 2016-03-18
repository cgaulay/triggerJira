'''
Created on 18 nov. 2015

@author: cgaulaynewpj
'''

##CONSTANTES
ip_dashboard = "cd.pagesjaunes.fr"
port_api_polarion = "8080"
path_workitem = "/workitems/"
path_testruns = "/testruns/"
#project_id = "front_pj_fd"
projects = ['front', 'orc', 'worc', 'api']
criticiteMap = [{"polarion" : "critical", "jira" :"Bloquant"}, {"polarion" : "major", "jira" : "Majeur"}, {"polarion" : "minor", "jira" :"error"}, {"polarion" : "trivial", "jira" : "error"}]
####################################
##ERREURS
E1 = "Le champ ID-Campagne devrait être rempli. "
E2 = "Le champ ID-cas-de-test devrait être rempli. "
E3 = "Pas de workitem trouvé dans le repository de Polarion. "
E4 = "Incohérence de criticité entre le test dans Polarion et JIRA. "
E5 = "Pas de testrun trouvé dans le repository du projet Polarion. "
E6 = "Pas de workitem trouvé dans le testrun. "
E7 = "Le champ \"Projet(s) Polarion\" ne doit contenir qu\'un seul projet. "
E8 = "Problème avec l\'api-polarion. Code : "
E9 = "Le test n\'est pas en succès dans le testrun."
####################################
##IMPORTS
import urllib2
from com.xhaus.jyson import JysonCodec as json
from java.util import Locale
from com.atlassian.jira import ComponentManager
from com.atlassian.jira.issue import CustomFieldManager
from com.atlassian.jira.project import ProjectManager
from com.atlassian.jira.issue.fields import CustomField
from operator import itemgetter
import httplib
import datetime
#####################################
##VARIABLES DE CLASSE
project_id = ""
workitem = ""
testrun = ""
workitem_id = ""
testrun_id= ""
WorkitemCreationDate = ""
WorkitemUpdatedDate = ""
description = u'ERREUR : Transition vers l\'état suivant impossible. '
cfm = ComponentManager.getInstance().getCustomFieldManager()
criticite = issue.getPriorityObject().getName()
provenance = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("Provenance"))
dateCreationJira = issue.getCreated().toString()
defect_id = issue.getKey()
#####################################
### METHODES
def throwError(P_error, P_field_name, P_field_error, P_field_value):
    global result
    global description
    if P_field_name is not None:
        invalid_fields['customfield_' + str(cfm.getCustomFieldObjectByName(P_field_name).getIdAsLong())] = P_field_error + P_field_value
    log.error('[' + defect_id + ']' + E8 + P_error)
    description = description + E8 + P_error
    result = False
    sendMetrics(P_field_error)


#verirication des champs requis
def checkRequiredFields():
    global workitem_id
    global testrun_id
    global cfm
    global result
    global project_id
    global description
    getProjectName()
    if result == False:
        return False
    testrun_id = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("ID-Campagne"))
    workitem_id = issue.getCustomFieldValue(cfm.getCustomFieldObjectByName("ID-cas-de-test"))
    if repr(testrun_id) == 'None' or not bool(testrun_id.lstrip()):
        log.error('[' + defect_id + ']' + E1)
        result = False
        invalid_fields['customfield_' + str(cfm.getCustomFieldObjectByName("ID-Campagne").getIdAsLong())] = u'Le champ ID-Campagne devrait être rempli'
        sendMetrics(E1)
    elif repr(workitem_id) == 'None' or not bool(workitem_id.lstrip()):
        log.error('[' + defect_id + ']' + E2)
        result = False
        invalid_fields['customfield_' + str(cfm.getCustomFieldObjectByName("ID-cas-de-test").getIdAsLong())] = u'Le champ ID-cas-de-test devrait être rempli'
        sendMetrics(E2)
    else:
        testrun_id = testrun_id.strip()
        workitem_id = workitem_id.strip()
        return True


#Recuperation d'un workitem par son id
def getWorkitem(P_id_workitem):
    global workitem
    global description
    global WorkitemUpdatedDate
    global WorkitemCreationDate
    global result
    try:
        r = urllib2.urlopen("http://" + ip_dashboard + "/api-polarion-1/" + path_workitem + P_id_workitem)
        workitem = r.read()
        WorkitemCreationDate = getWorkitemCreationDate(workitem)
        WorkitemUpdatedDate = getWorkitemUpdatedDate(workitem)
    except urllib2.HTTPError, httpError:
        print 'HTTPError'
        try:
            data = json.loads(httpError.read())
            error = data["status"]["status_content"][0]["message"]
            throwError(error, "ID-cas-de-test", E3, P_id_workitem)
        except:
            log.error('[' + defect_id + ']' + E8 + str(httpError))
            description = description + E8 + str(httpError)
            sendMetrics(str(httpError))
            result = False
    except urllib2.URLError, urlError:
        print 'URLError'
        throwError(str(urlError.reason), "ID-cas-de-test", E3, P_id_workitem)
    except Exception, e:
        print 'Exception'
        throwError(str(e), "ID-cas-de-test", E3, P_id_workitem)
    return workitem

#Verification de la coherence de criticite entre jira et polarion
def checkCriticity(P_criticite,P_workitem):
    global result
    global description
    data = json.loads(P_workitem)

    customMap = data["customFields"]["Custom"]
    indexCriticiteWorkitem = map(itemgetter('key'), customMap).index('criticality')
    criticiteWorkitem = customMap[indexCriticiteWorkitem]["value"]["id"]
    indexCriticite = map(itemgetter('polarion'), criticiteMap).index(criticiteWorkitem)

    if criticiteMap[indexCriticite].get("jira") != P_criticite:
        log.error('[' + defect_id + ']' + E4)
        result = False
        description = u'ERREUR : Incohérence de criticité entre JIRA ' + defect_id + ' (' + P_criticite + ') et le test Polarion ' + workitem_id + ' (' + criticiteWorkitem + ')'
        sendMetrics(E4)
    else:
        result = True

def getTestRun(P_id_testruns, P_project_id):
    global project_id
    global testrun
    try:
        r = urllib2.urlopen("http://" + ip_dashboard + "/api-polarion-1/" + path_testruns + "?id=" + P_id_testruns + "&project=" + P_project_id)
        testrun = r.read()
    except urllib2.HTTPError, httpError:
        print 'HTTPError'
        data = json.loads(httpError.read())
        error = data["status"]["status_content"][0]["message"]
        throwError(error, "ID-Campagne", E5, P_id_testruns)
    except urllib2.URLError, urlError:
        print 'URLError'
        throwError(str(urlError.reason), "ID-Campagne", E8 + str(urlError.reason), P_id_testruns)
    except Exception, e:
        print 'Exception'
        throwError(str(e), "ID-Campagne", E5, P_id_testruns)
    return testrun

def checkWorkitemInTestRun(P_id_workitem, P_testrun):
    global result
    if P_testrun.find(P_id_workitem) == -1:
        log.error('[' + defect_id + '] Pas de workitem ayant l\'id [' + P_id_workitem + '] trouvé dans le testrun.')
        result = False
        invalid_fields['customfield_' + str(cfm.getCustomFieldObjectByName("ID-cas-de-test").getIdAsLong())] = u'Le workitem ayant l\'id [' + P_id_workitem + '] n\'a pas été trouvé dans le testrun [ '+ testrun_id + ' ].'
        sendMetrics(E6)
    else:
        result = True
        return True

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
            result = True
    else:
        project_id = originalIssue.getProjectObject().getName()
        result = True

#getCreationDate workitem
def getWorkitemCreationDate(P_workitem):
    data = json.loads(P_workitem)
    dateCreationWorkitem = data["created"]
    return dateCreationWorkitem

#getCreationDate workitem
def getWorkitemUpdatedDate(P_workitem):
    data = json.loads(P_workitem)
    dateUpdatedWorkitem = data["updated"]
    return dateUpdatedWorkitem

#envoyer les metriques au dashboard
def sendMetrics(P_error):
    global  project_id
    global result
    now = datetime.datetime.today()
    JiraCreationDate = datetime.datetime.strptime(dateCreationJira, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S') + '+01:00'

    params = {}
    params["criticality"] = criticite
    params["date"] = now.strftime('%Y-%m-%dT%H:%M') + '+01:00'
    params["defect_id"] = defect_id
    params["defect_project"] = str(project_id)
    params["error_message"] = P_error
    params["status"] = result
    params["testcase_id"] = workitem_id
    params["testrun_id"] = testrun_id
    params["date_created_jira"] = JiraCreationDate
    params["date_created_test"] = WorkitemCreationDate
    params["date_updated_test"] = WorkitemUpdatedDate
    params["type"] = provenance
    params = json.dumps(params)
    #print params

    headers = {}
    headers['Content-Type'] = "application/json"
    headers['Accept'] = "application/json"
    try:
        conn = httplib.HTTPConnection(ip_dashboard)
        conn.request('PUT', '/dashboard-cd/api/measure/defect', params, headers)
        response = conn.getresponse()
        log.info('[' + defect_id + '] Envoi des indicateurs : ' + response.reason )
    except Exception, e:
        log.warn(u'Impossible d\'envoyer les métriques : ' + str(e))
        pass

#Vérifier le résultat du test dans le testrun
def checkTestSuccess(P_testrun, P_id_workitem):
    global result
    global description
    data = json.loads(P_testrun)
    customMap = data["records"]["TestRecord"]
    mapWorkitem = map(itemgetter('testCaseURI'), customMap)
    indexe = [ i for i, word in enumerate(mapWorkitem) if word.endswith(P_id_workitem) ]
    result = data["records"]["TestRecord"][indexe[0]]["result"]["id"]
    if result == 'passed':
        return True
    else:
        log.error('[' + defect_id + '] Le test devrait être en succès dans le testrun.')
        result = False
        invalid_fields['customfield_' + str(cfm.getCustomFieldObjectByName("ID-cas-de-test").getIdAsLong())] = u'Le workitem ayant l\'id [' + P_id_workitem + '] devrait être en succès dans le testrun [ '+ testrun_id + ' ].'
        sendMetrics(E9)
    return False

###FIN METHODES

##DEBUT DU TRIGGER
debutTraitement = datetime.datetime.now()
log.info('[' + defect_id + '] DEBUT DU TRIGGER')
if checkRequiredFields() == True:
    log.info('[' + defect_id + '] Champs requis OK')
    workitem = getWorkitem(workitem_id)
    if result == True:
        log.info('[' + defect_id + '] Test OK dans Polarion')
        testrun = getTestRun(testrun_id,project_id)
        if result == True:
            checkWorkitemInTestRun(workitem_id, testrun)
            if result == True:
                log.info('[' + defect_id + '] Test existant dans le testrun dans Polarion')
                if checkTestSuccess(testrun, workitem_id) == True:
                    log.info('[' + defect_id + '] Résultat du test OK dans le testrun dans Polarion')
                    checkCriticity(criticite, workitem)
                    if result == True:
                        log.info('[' + defect_id + '] Coherence de criticite OK')
                        sendMetrics("")
finTraitement = datetime.datetime.now()
duree = finTraitement - debutTraitement
log.info('[' + defect_id + '] FIN DU TRIGGER en ' + str(duree) )