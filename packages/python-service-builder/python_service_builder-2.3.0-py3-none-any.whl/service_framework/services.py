# Copyright 2022 David Harcombe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import aenum as enum

from service_framework import ServiceDefinition
from service_framework.service_finder import ServiceFinder


class Service(enum.Enum):
  """Defines the generic Enum for any service.
  """

  @property
  def definition(self) -> ServiceDefinition:
    """Fetch the ServiceDefinition.

    Lazily returns the dataclass containing the service definition
    details. It has to be lazy, as it can't be defined at
    initialization time.

    Returns:
        ServiceDefinition: the service definition
    """
    return self._value_

  @classmethod
  def create_service(cls, name: str) -> Service:
    """ Finds a named service

    This function finds a named service in the list of publicly available
    Google discovery documents if it is not in the current Enum of services.
    The service is then added to the Enum for the current program scope.

    If the service does not exist, an exception will be thrown.

    Returns:
        Service: The new service Enum
    """
    finder = ServiceFinder()
    if service := finder(name):
      new_service = object.__new__(cls)
      new_service._name_ = name.upper()
      new_service._value_ = service
      cls._value2member_map_[name.upper()] = new_service
      return new_service

  @classmethod
  def _missing_(cls, value) -> Service:
    """Handle a request for a missing ordinal

    This handles the case where a developer requests a service using the syntax
    `services.Service('FOO')`
    and `FOO` is not a service present in the Enum.

    The system attempts to fetch a list of all Google services and retrieve
    the definition for the desired service by name.

    If the service does not exist at all, then an `Exception` is raised.

    Args:
        value (str): The name of the missing service

    Raises:
        Exception: no service found

    Returns:
        Service: a filled out Enum for thge missing `Service`
    """
    if service := cls.__members__.get(value.upper(), None):
      return service
    else:
      return cls.create_service(value)

  @classmethod
  def from_value(cls, value: str) -> Service:
    """Creates a service enum from the name of the service.

    This will return a pre-defined service from the Enum if it exists, but will
    search for a services if the specified name is missing from the `Services`
    enum.

    Args:
        value (str): the service name

    Raises:
        Exception: no service found

    Returns:
        S: the service definition
    """
    if service := cls.__members__.get(value.upper(), None):
      return service

    else:
      return cls.create_service(value)

  # DO NOT REMOVE THE LINE BELOW - THIS IS THE MARKER FOR AUTO-FETCH
  # SERVICE DEFINITIONS: 2026-01-16 21:12:15
  ABUSIVEEXPERIENCEREPORT = ServiceDefinition(service_name='abusiveexperiencereport', version='v1', discovery_service_url='https://abusiveexperiencereport.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ACCELERATEDMOBILEPAGEURL = ServiceDefinition(service_name='acceleratedmobilepageurl', version='v1', discovery_service_url='https://acceleratedmobilepageurl.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ACCESSAPPROVAL = ServiceDefinition(service_name='accessapproval', version='v1', discovery_service_url='https://accessapproval.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ACCESSCONTEXTMANAGER = ServiceDefinition(service_name='accesscontextmanager', version='v1', discovery_service_url='https://accesscontextmanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ADDRESSVALIDATION = ServiceDefinition(service_name='addressvalidation', version='v1', discovery_service_url='https://addressvalidation.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ADEXCHANGEBUYER2 = ServiceDefinition(service_name='adexchangebuyer2', version='v2beta1', discovery_service_url='https://adexchangebuyer.googleapis.com/$discovery/rest?version=v2beta1')  # nopep8
  ADEXPERIENCEREPORT = ServiceDefinition(service_name='adexperiencereport', version='v1', discovery_service_url='https://adexperiencereport.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ADMIN = ServiceDefinition(service_name='admin', version='reports_v1', discovery_service_url='https://admin.googleapis.com/$discovery/rest?version=reports_v1')  # nopep8
  ADMOB = ServiceDefinition(service_name='admob', version='v1', discovery_service_url='https://admob.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ADSENSE = ServiceDefinition(service_name='adsense', version='v2', discovery_service_url='https://adsense.googleapis.com/$discovery/rest?version=v2')  # nopep8
  ADSENSEPLATFORM = ServiceDefinition(service_name='adsenseplatform', version='v1', discovery_service_url='https://adsenseplatform.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ADVISORYNOTIFICATIONS = ServiceDefinition(service_name='advisorynotifications', version='v1', discovery_service_url='https://advisorynotifications.googleapis.com/$discovery/rest?version=v1')  # nopep8
  AIPLATFORM = ServiceDefinition(service_name='aiplatform', version='v1', discovery_service_url='https://aiplatform.googleapis.com/$discovery/rest?version=v1')  # nopep8
  AIRQUALITY = ServiceDefinition(service_name='airquality', version='v1', discovery_service_url='https://airquality.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ALERTCENTER = ServiceDefinition(service_name='alertcenter', version='v1beta1', discovery_service_url='https://alertcenter.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  ALLOYDB = ServiceDefinition(service_name='alloydb', version='v1', discovery_service_url='https://alloydb.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ANALYTICS = ServiceDefinition(service_name='analytics', version='v3', discovery_service_url='https://analytics.googleapis.com/$discovery/rest?version=v3')  # nopep8
  ANALYTICSADMIN = ServiceDefinition(service_name='analyticsadmin', version='v1beta', discovery_service_url='https://analyticsadmin.googleapis.com/$discovery/rest?version=v1beta')  # nopep8
  ANALYTICSDATA = ServiceDefinition(service_name='analyticsdata', version='v1beta', discovery_service_url='https://analyticsdata.googleapis.com/$discovery/rest?version=v1beta')  # nopep8
  ANALYTICSHUB = ServiceDefinition(service_name='analyticshub', version='v1', discovery_service_url='https://analyticshub.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ANDROIDDEVICEPROVISIONING = ServiceDefinition(service_name='androiddeviceprovisioning', version='v1', discovery_service_url='https://androiddeviceprovisioning.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ANDROIDENTERPRISE = ServiceDefinition(service_name='androidenterprise', version='v1', discovery_service_url='https://androidenterprise.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ANDROIDMANAGEMENT = ServiceDefinition(service_name='androidmanagement', version='v1', discovery_service_url='https://androidmanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ANDROIDPUBLISHER = ServiceDefinition(service_name='androidpublisher', version='v3', discovery_service_url='https://androidpublisher.googleapis.com/$discovery/rest?version=v3')  # nopep8
  APIGATEWAY = ServiceDefinition(service_name='apigateway', version='v1', discovery_service_url='https://apigateway.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APIGEE = ServiceDefinition(service_name='apigee', version='v1', discovery_service_url='https://apigee.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APIGEEREGISTRY = ServiceDefinition(service_name='apigeeregistry', version='v1', discovery_service_url='https://apigeeregistry.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APIHUB = ServiceDefinition(service_name='apihub', version='v1', discovery_service_url='https://apihub.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APIKEYS = ServiceDefinition(service_name='apikeys', version='v2', discovery_service_url='https://apikeys.googleapis.com/$discovery/rest?version=v2')  # nopep8
  APIM = ServiceDefinition(service_name='apim', version='v1alpha', discovery_service_url='https://apim.googleapis.com/$discovery/rest?version=v1alpha')  # nopep8
  APPENGINE = ServiceDefinition(service_name='appengine', version='v1', discovery_service_url='https://appengine.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APPHUB = ServiceDefinition(service_name='apphub', version='v1', discovery_service_url='https://apphub.googleapis.com/$discovery/rest?version=v1')  # nopep8
  APPSMARKET = ServiceDefinition(service_name='appsmarket', version='v2', discovery_service_url='https://appsmarket.googleapis.com/$discovery/rest?version=v2')  # nopep8
  AREA120TABLES = ServiceDefinition(service_name='area120tables', version='v1alpha1', discovery_service_url='https://area120tables.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  AREAINSIGHTS = ServiceDefinition(service_name='areainsights', version='v1', discovery_service_url='https://areainsights.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ARTIFACTREGISTRY = ServiceDefinition(service_name='artifactregistry', version='v1', discovery_service_url='https://artifactregistry.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ASSUREDWORKLOADS = ServiceDefinition(service_name='assuredworkloads', version='v1', discovery_service_url='https://assuredworkloads.googleapis.com/$discovery/rest?version=v1')  # nopep8
  AUTHORIZEDBUYERSMARKETPLACE = ServiceDefinition(service_name='authorizedbuyersmarketplace', version='v1', discovery_service_url='https://authorizedbuyersmarketplace.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BACKUPDR = ServiceDefinition(service_name='backupdr', version='v1', discovery_service_url='https://backupdr.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BAREMETALSOLUTION = ServiceDefinition(service_name='baremetalsolution', version='v2', discovery_service_url='https://baremetalsolution.googleapis.com/$discovery/rest?version=v2')  # nopep8
  BATCH = ServiceDefinition(service_name='batch', version='v1', discovery_service_url='https://batch.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BEYONDCORP = ServiceDefinition(service_name='beyondcorp', version='v1', discovery_service_url='https://beyondcorp.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BIGLAKE = ServiceDefinition(service_name='biglake', version='v1', discovery_service_url='https://biglake.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BIGQUERY = ServiceDefinition(service_name='bigquery', version='v2', discovery_service_url='https://bigquery.googleapis.com/$discovery/rest?version=v2')  # nopep8
  BIGQUERYCONNECTION = ServiceDefinition(service_name='bigqueryconnection', version='v1', discovery_service_url='https://bigqueryconnection.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BIGQUERYDATAPOLICY = ServiceDefinition(service_name='bigquerydatapolicy', version='v2', discovery_service_url='https://bigquerydatapolicy.googleapis.com/$discovery/rest?version=v2')  # nopep8
  BIGQUERYDATATRANSFER = ServiceDefinition(service_name='bigquerydatatransfer', version='v1', discovery_service_url='https://bigquerydatatransfer.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BIGQUERYRESERVATION = ServiceDefinition(service_name='bigqueryreservation', version='v1', discovery_service_url='https://bigqueryreservation.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BIGTABLEADMIN = ServiceDefinition(service_name='bigtableadmin', version='v2', discovery_service_url='https://bigtableadmin.googleapis.com/$discovery/rest?version=v2')  # nopep8
  BILLINGBUDGETS = ServiceDefinition(service_name='billingbudgets', version='v1', discovery_service_url='https://billingbudgets.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BINARYAUTHORIZATION = ServiceDefinition(service_name='binaryauthorization', version='v1', discovery_service_url='https://binaryauthorization.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BLOCKCHAINNODEENGINE = ServiceDefinition(service_name='blockchainnodeengine', version='v1', discovery_service_url='https://blockchainnodeengine.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BLOGGER = ServiceDefinition(service_name='blogger', version='v3', discovery_service_url='https://blogger.googleapis.com/$discovery/rest?version=v3')  # nopep8
  BOOKS = ServiceDefinition(service_name='books', version='v1', discovery_service_url='https://books.googleapis.com/$discovery/rest?version=v1')  # nopep8
  BUSINESSPROFILEPERFORMANCE = ServiceDefinition(service_name='businessprofileperformance', version='v1', discovery_service_url='https://businessprofileperformance.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CALENDAR = ServiceDefinition(service_name='calendar', version='v3', discovery_service_url='https://calendar-json.googleapis.com/$discovery/rest?version=v3')  # nopep8
  CERTIFICATEMANAGER = ServiceDefinition(service_name='certificatemanager', version='v1', discovery_service_url='https://certificatemanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CHAT = ServiceDefinition(service_name='chat', version='v1', discovery_service_url='https://chat.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CHECKS = ServiceDefinition(service_name='checks', version='v1alpha', discovery_service_url='https://checks.googleapis.com/$discovery/rest?version=v1alpha')  # nopep8
  CHROMEMANAGEMENT = ServiceDefinition(service_name='chromemanagement', version='v1', discovery_service_url='https://chromemanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CHROMEPOLICY = ServiceDefinition(service_name='chromepolicy', version='v1', discovery_service_url='https://chromepolicy.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CHROMEUXREPORT = ServiceDefinition(service_name='chromeuxreport', version='v1', discovery_service_url='https://chromeuxreport.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CHROMEWEBSTORE = ServiceDefinition(service_name='chromewebstore', version='v2', discovery_service_url='https://chromewebstore.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CIVICINFO = ServiceDefinition(service_name='civicinfo', version='v2', discovery_service_url='https://civicinfo.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLASSROOM = ServiceDefinition(service_name='classroom', version='v1', discovery_service_url='https://classroom.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDASSET = ServiceDefinition(service_name='cloudasset', version='v1', discovery_service_url='https://cloudasset.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDBILLING = ServiceDefinition(service_name='cloudbilling', version='v1', discovery_service_url='https://cloudbilling.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDBUILD = ServiceDefinition(service_name='cloudbuild', version='v2', discovery_service_url='https://cloudbuild.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLOUDCHANNEL = ServiceDefinition(service_name='cloudchannel', version='v1', discovery_service_url='https://cloudchannel.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDCOMMERCEPROCUREMENT = ServiceDefinition(service_name='cloudcommerceprocurement', version='v1', discovery_service_url='https://cloudcommerceprocurement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDCONTROLSPARTNER = ServiceDefinition(service_name='cloudcontrolspartner', version='v1', discovery_service_url='https://cloudcontrolspartner.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDDEPLOY = ServiceDefinition(service_name='clouddeploy', version='v1', discovery_service_url='https://clouddeploy.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDERRORREPORTING = ServiceDefinition(service_name='clouderrorreporting', version='v1beta1', discovery_service_url='https://clouderrorreporting.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  CLOUDFUNCTIONS = ServiceDefinition(service_name='cloudfunctions', version='v2', discovery_service_url='https://cloudfunctions.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLOUDIDENTITY = ServiceDefinition(service_name='cloudidentity', version='v1', discovery_service_url='https://cloudidentity.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDKMS = ServiceDefinition(service_name='cloudkms', version='v1', discovery_service_url='https://cloudkms.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDLOCATIONFINDER = ServiceDefinition(service_name='cloudlocationfinder', version='v1', discovery_service_url='https://cloudlocationfinder.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDPROFILER = ServiceDefinition(service_name='cloudprofiler', version='v2', discovery_service_url='https://cloudprofiler.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLOUDRESOURCEMANAGER = ServiceDefinition(service_name='cloudresourcemanager', version='v3', discovery_service_url='https://cloudresourcemanager.googleapis.com/$discovery/rest?version=v3')  # nopep8
  CLOUDSCHEDULER = ServiceDefinition(service_name='cloudscheduler', version='v1', discovery_service_url='https://cloudscheduler.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDSEARCH = ServiceDefinition(service_name='cloudsearch', version='v1', discovery_service_url='https://cloudsearch.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDSHELL = ServiceDefinition(service_name='cloudshell', version='v1', discovery_service_url='https://cloudshell.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CLOUDSUPPORT = ServiceDefinition(service_name='cloudsupport', version='v2', discovery_service_url='https://cloudsupport.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLOUDTASKS = ServiceDefinition(service_name='cloudtasks', version='v2', discovery_service_url='https://cloudtasks.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CLOUDTRACE = ServiceDefinition(service_name='cloudtrace', version='v2', discovery_service_url='https://cloudtrace.googleapis.com/$discovery/rest?version=v2')  # nopep8
  COMPOSER = ServiceDefinition(service_name='composer', version='v1', discovery_service_url='https://composer.googleapis.com/$discovery/rest?version=v1')  # nopep8
  COMPUTE = ServiceDefinition(service_name='compute', version='v1', discovery_service_url='https://www.googleapis.com/discovery/v1/apis/compute/v1/rest')  # nopep8
  CONFIG = ServiceDefinition(service_name='config', version='v1', discovery_service_url='https://config.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CONNECTORS = ServiceDefinition(service_name='connectors', version='v2', discovery_service_url='https://connectors.googleapis.com/$discovery/rest?version=v2')  # nopep8
  CONTACTCENTERAIPLATFORM = ServiceDefinition(service_name='contactcenteraiplatform', version='v1alpha1', discovery_service_url='https://contactcenteraiplatform.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  CONTACTCENTERINSIGHTS = ServiceDefinition(service_name='contactcenterinsights', version='v1', discovery_service_url='https://contactcenterinsights.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CONTAINER = ServiceDefinition(service_name='container', version='v1', discovery_service_url='https://container.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CONTAINERANALYSIS = ServiceDefinition(service_name='containeranalysis', version='v1', discovery_service_url='https://containeranalysis.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CONTENT = ServiceDefinition(service_name='content', version='v2.1', discovery_service_url='https://shoppingcontent.googleapis.com/$discovery/rest?version=v2.1')  # nopep8
  CONTENTWAREHOUSE = ServiceDefinition(service_name='contentwarehouse', version='v1', discovery_service_url='https://contentwarehouse.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CSS = ServiceDefinition(service_name='css', version='v1', discovery_service_url='https://css.googleapis.com/$discovery/rest?version=v1')  # nopep8
  CUSTOMSEARCH = ServiceDefinition(service_name='customsearch', version='v1', discovery_service_url='https://customsearch.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATACATALOG = ServiceDefinition(service_name='datacatalog', version='v1', discovery_service_url='https://datacatalog.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAFLOW = ServiceDefinition(service_name='dataflow', version='v1b3', discovery_service_url='https://dataflow.googleapis.com/$discovery/rest?version=v1b3')  # nopep8
  DATAFORM = ServiceDefinition(service_name='dataform', version='v1', discovery_service_url='https://dataform.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAFUSION = ServiceDefinition(service_name='datafusion', version='v1', discovery_service_url='https://datafusion.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATALABELING = ServiceDefinition(service_name='datalabeling', version='v1beta1', discovery_service_url='https://datalabeling.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  DATALINEAGE = ServiceDefinition(service_name='datalineage', version='v1', discovery_service_url='https://datalineage.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAMANAGER = ServiceDefinition(service_name='datamanager', version='v1', discovery_service_url='https://datamanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAMIGRATION = ServiceDefinition(service_name='datamigration', version='v1', discovery_service_url='https://datamigration.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAPIPELINES = ServiceDefinition(service_name='datapipelines', version='v1', discovery_service_url='https://datapipelines.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAPLEX = ServiceDefinition(service_name='dataplex', version='v1', discovery_service_url='https://dataplex.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAPORTABILITY = ServiceDefinition(service_name='dataportability', version='v1', discovery_service_url='https://dataportability.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATAPROC = ServiceDefinition(service_name='dataproc', version='v1', discovery_service_url='https://dataproc.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATASTORE = ServiceDefinition(service_name='datastore', version='v1', discovery_service_url='https://datastore.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DATASTREAM = ServiceDefinition(service_name='datastream', version='v1', discovery_service_url='https://datastream.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DEPLOYMENTMANAGER = ServiceDefinition(service_name='deploymentmanager', version='v2', discovery_service_url='https://deploymentmanager.googleapis.com/$discovery/rest?version=v2')  # nopep8
  DEVELOPERCONNECT = ServiceDefinition(service_name='developerconnect', version='v1', discovery_service_url='https://developerconnect.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DFAREPORTING = ServiceDefinition(service_name='dfareporting', version='v5', discovery_service_url='https://dfareporting.googleapis.com/$discovery/rest?version=v5')  # nopep8
  DIALOGFLOW = ServiceDefinition(service_name='dialogflow', version='v3', discovery_service_url='https://dialogflow.googleapis.com/$discovery/rest?version=v3')  # nopep8
  DIGITALASSETLINKS = ServiceDefinition(service_name='digitalassetlinks', version='v1', discovery_service_url='https://digitalassetlinks.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DISCOVERY = ServiceDefinition(service_name='discovery', version='v1', discovery_service_url='https://discovery.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DISCOVERYENGINE = ServiceDefinition(service_name='discoveryengine', version='v1', discovery_service_url='https://discoveryengine.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DISPLAYVIDEO = ServiceDefinition(service_name='displayvideo', version='v4', discovery_service_url='https://displayvideo.googleapis.com/$discovery/rest?version=v4')  # nopep8
  DLP = ServiceDefinition(service_name='dlp', version='v2', discovery_service_url='https://dlp.googleapis.com/$discovery/rest?version=v2')  # nopep8
  DNS = ServiceDefinition(service_name='dns', version='v1', discovery_service_url='https://dns.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DOCS = ServiceDefinition(service_name='docs', version='v1', discovery_service_url='https://docs.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DOCUMENTAI = ServiceDefinition(service_name='documentai', version='v1', discovery_service_url='https://documentai.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DOMAINS = ServiceDefinition(service_name='domains', version='v1', discovery_service_url='https://domains.googleapis.com/$discovery/rest?version=v1')  # nopep8
  DOUBLECLICKBIDMANAGER = ServiceDefinition(service_name='doubleclickbidmanager', version='v2', discovery_service_url='https://doubleclickbidmanager.googleapis.com/$discovery/rest?version=v2')  # nopep8
  DOUBLECLICKSEARCH = ServiceDefinition(service_name='doubleclicksearch', version='v2', discovery_service_url='https://doubleclicksearch.googleapis.com/$discovery/rest?version=v2')  # nopep8
  DRIVE = ServiceDefinition(service_name='drive', version='v3', discovery_service_url='https://www.googleapis.com/discovery/v1/apis/drive/v3/rest')  # nopep8
  DRIVEACTIVITY = ServiceDefinition(service_name='driveactivity', version='v2', discovery_service_url='https://driveactivity.googleapis.com/$discovery/rest?version=v2')  # nopep8
  DRIVELABELS = ServiceDefinition(service_name='drivelabels', version='v2', discovery_service_url='https://drivelabels.googleapis.com/$discovery/rest?version=v2')  # nopep8
  ESSENTIALCONTACTS = ServiceDefinition(service_name='essentialcontacts', version='v1', discovery_service_url='https://essentialcontacts.googleapis.com/$discovery/rest?version=v1')  # nopep8
  EVENTARC = ServiceDefinition(service_name='eventarc', version='v1', discovery_service_url='https://eventarc.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FACTCHECKTOOLS = ServiceDefinition(service_name='factchecktools', version='v1alpha1', discovery_service_url='https://factchecktools.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  FCM = ServiceDefinition(service_name='fcm', version='v1', discovery_service_url='https://fcm.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FCMDATA = ServiceDefinition(service_name='fcmdata', version='v1beta1', discovery_service_url='https://fcmdata.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  FILE = ServiceDefinition(service_name='file', version='v1', discovery_service_url='https://file.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASE = ServiceDefinition(service_name='firebase', version='v1beta1', discovery_service_url='https://firebase.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  FIREBASEAPPCHECK = ServiceDefinition(service_name='firebaseappcheck', version='v1', discovery_service_url='https://firebaseappcheck.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEAPPDISTRIBUTION = ServiceDefinition(service_name='firebaseappdistribution', version='v1', discovery_service_url='https://firebaseappdistribution.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEAPPHOSTING = ServiceDefinition(service_name='firebaseapphosting', version='v1', discovery_service_url='https://firebaseapphosting.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEDATABASE = ServiceDefinition(service_name='firebasedatabase', version='v1beta', discovery_service_url='https://firebasedatabase.googleapis.com/$discovery/rest?version=v1beta')  # nopep8
  FIREBASEDATACONNECT = ServiceDefinition(service_name='firebasedataconnect', version='v1', discovery_service_url='https://firebasedataconnect.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEDYNAMICLINKS = ServiceDefinition(service_name='firebasedynamiclinks', version='v1', discovery_service_url='https://firebasedynamiclinks.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEHOSTING = ServiceDefinition(service_name='firebasehosting', version='v1', discovery_service_url='https://firebasehosting.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASEML = ServiceDefinition(service_name='firebaseml', version='v1', discovery_service_url='https://firebaseml.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASERULES = ServiceDefinition(service_name='firebaserules', version='v1', discovery_service_url='https://firebaserules.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FIREBASESTORAGE = ServiceDefinition(service_name='firebasestorage', version='v1beta', discovery_service_url='https://firebasestorage.googleapis.com/$discovery/rest?version=v1beta')  # nopep8
  FIRESTORE = ServiceDefinition(service_name='firestore', version='v1', discovery_service_url='https://firestore.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FITNESS = ServiceDefinition(service_name='fitness', version='v1', discovery_service_url='https://fitness.googleapis.com/$discovery/rest?version=v1')  # nopep8
  FORMS = ServiceDefinition(service_name='forms', version='v1', discovery_service_url='https://forms.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GAMES = ServiceDefinition(service_name='games', version='v1', discovery_service_url='https://games.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GAMESCONFIGURATION = ServiceDefinition(service_name='gamesConfiguration', version='v1configuration', discovery_service_url='https://gamesconfiguration.googleapis.com/$discovery/rest?version=v1configuration')  # nopep8
  GAMESMANAGEMENT = ServiceDefinition(service_name='gamesManagement', version='v1management', discovery_service_url='https://gamesmanagement.googleapis.com/$discovery/rest?version=v1management')  # nopep8
  GKEBACKUP = ServiceDefinition(service_name='gkebackup', version='v1', discovery_service_url='https://gkebackup.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GKEHUB = ServiceDefinition(service_name='gkehub', version='v2', discovery_service_url='https://gkehub.googleapis.com/$discovery/rest?version=v2')  # nopep8
  GKEONPREM = ServiceDefinition(service_name='gkeonprem', version='v1', discovery_service_url='https://gkeonprem.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GMAIL = ServiceDefinition(service_name='gmail', version='v1', discovery_service_url='https://gmail.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GMAILPOSTMASTERTOOLS = ServiceDefinition(service_name='gmailpostmastertools', version='v1', discovery_service_url='https://gmailpostmastertools.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GROUPSMIGRATION = ServiceDefinition(service_name='groupsmigration', version='v1', discovery_service_url='https://groupsmigration.googleapis.com/$discovery/rest?version=v1')  # nopep8
  GROUPSSETTINGS = ServiceDefinition(service_name='groupssettings', version='v1', discovery_service_url='https://groupssettings.googleapis.com/$discovery/rest?version=v1')  # nopep8
  HEALTHCARE = ServiceDefinition(service_name='healthcare', version='v1', discovery_service_url='https://healthcare.googleapis.com/$discovery/rest?version=v1')  # nopep8
  HOMEGRAPH = ServiceDefinition(service_name='homegraph', version='v1', discovery_service_url='https://homegraph.googleapis.com/$discovery/rest?version=v1')  # nopep8
  IAM = ServiceDefinition(service_name='iam', version='v2', discovery_service_url='https://iam.googleapis.com/$discovery/rest?version=v2')  # nopep8
  IAMCREDENTIALS = ServiceDefinition(service_name='iamcredentials', version='v1', discovery_service_url='https://iamcredentials.googleapis.com/$discovery/rest?version=v1')  # nopep8
  IAP = ServiceDefinition(service_name='iap', version='v1', discovery_service_url='https://iap.googleapis.com/$discovery/rest?version=v1')  # nopep8
  IDENTITYTOOLKIT = ServiceDefinition(service_name='identitytoolkit', version='v3', discovery_service_url='https://identitytoolkit.googleapis.com/$discovery/rest?version=v3')  # nopep8
  IDS = ServiceDefinition(service_name='ids', version='v1', discovery_service_url='https://ids.googleapis.com/$discovery/rest?version=v1')  # nopep8
  INDEXING = ServiceDefinition(service_name='indexing', version='v3', discovery_service_url='https://indexing.googleapis.com/$discovery/rest?version=v3')  # nopep8
  INTEGRATIONS = ServiceDefinition(service_name='integrations', version='v1', discovery_service_url='https://integrations.googleapis.com/$discovery/rest?version=v1')  # nopep8
  JOBS = ServiceDefinition(service_name='jobs', version='v4', discovery_service_url='https://jobs.googleapis.com/$discovery/rest?version=v4')  # nopep8
  KEEP = ServiceDefinition(service_name='keep', version='v1', discovery_service_url='https://keep.googleapis.com/$discovery/rest?version=v1')  # nopep8
  KGSEARCH = ServiceDefinition(service_name='kgsearch', version='v1', discovery_service_url='https://kgsearch.googleapis.com/$discovery/rest?version=v1')  # nopep8
  KMSINVENTORY = ServiceDefinition(service_name='kmsinventory', version='v1', discovery_service_url='https://kmsinventory.googleapis.com/$discovery/rest?version=v1')  # nopep8
  LANGUAGE = ServiceDefinition(service_name='language', version='v2', discovery_service_url='https://language.googleapis.com/$discovery/rest?version=v2')  # nopep8
  LIBRARYAGENT = ServiceDefinition(service_name='libraryagent', version='v1', discovery_service_url='https://libraryagent.googleapis.com/$discovery/rest?version=v1')  # nopep8
  LICENSING = ServiceDefinition(service_name='licensing', version='v1', discovery_service_url='https://licensing.googleapis.com/$discovery/rest?version=v1')  # nopep8
  LIFESCIENCES = ServiceDefinition(service_name='lifesciences', version='v2beta', discovery_service_url='https://lifesciences.googleapis.com/$discovery/rest?version=v2beta')  # nopep8
  LOCALSERVICES = ServiceDefinition(service_name='localservices', version='v1', discovery_service_url='https://localservices.googleapis.com/$discovery/rest?version=v1')  # nopep8
  LOGGING = ServiceDefinition(service_name='logging', version='v2', discovery_service_url='https://logging.googleapis.com/$discovery/rest?version=v2')  # nopep8
  LOOKER = ServiceDefinition(service_name='looker', version='v1', discovery_service_url='https://looker.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MANAGEDIDENTITIES = ServiceDefinition(service_name='managedidentities', version='v1', discovery_service_url='https://managedidentities.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MANAGEDKAFKA = ServiceDefinition(service_name='managedkafka', version='v1', discovery_service_url='https://managedkafka.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MANUFACTURERS = ServiceDefinition(service_name='manufacturers', version='v1', discovery_service_url='https://manufacturers.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MARKETINGPLATFORMADMIN = ServiceDefinition(service_name='marketingplatformadmin', version='v1alpha', discovery_service_url='https://marketingplatformadmin.googleapis.com/$discovery/rest?version=v1alpha')  # nopep8
  MEET = ServiceDefinition(service_name='meet', version='v2', discovery_service_url='https://meet.googleapis.com/$discovery/rest?version=v2')  # nopep8
  MEMCACHE = ServiceDefinition(service_name='memcache', version='v1', discovery_service_url='https://memcache.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MERCHANTAPI = ServiceDefinition(service_name='merchantapi', version='reviews_v1beta', discovery_service_url='https://merchantapi.googleapis.com/$discovery/rest?version=reviews_v1beta')  # nopep8
  METASTORE = ServiceDefinition(service_name='metastore', version='v2', discovery_service_url='https://metastore.googleapis.com/$discovery/rest?version=v2')  # nopep8
  MIGRATIONCENTER = ServiceDefinition(service_name='migrationcenter', version='v1', discovery_service_url='https://migrationcenter.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ML = ServiceDefinition(service_name='ml', version='v1', discovery_service_url='https://ml.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MONITORING = ServiceDefinition(service_name='monitoring', version='v3', discovery_service_url='https://monitoring.googleapis.com/$discovery/rest?version=v3')  # nopep8
  MYBUSINESSACCOUNTMANAGEMENT = ServiceDefinition(service_name='mybusinessaccountmanagement', version='v1', discovery_service_url='https://mybusinessaccountmanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSBUSINESSINFORMATION = ServiceDefinition(service_name='mybusinessbusinessinformation', version='v1', discovery_service_url='https://mybusinessbusinessinformation.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSLODGING = ServiceDefinition(service_name='mybusinesslodging', version='v1', discovery_service_url='https://mybusinesslodging.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSNOTIFICATIONS = ServiceDefinition(service_name='mybusinessnotifications', version='v1', discovery_service_url='https://mybusinessnotifications.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSPLACEACTIONS = ServiceDefinition(service_name='mybusinessplaceactions', version='v1', discovery_service_url='https://mybusinessplaceactions.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSQANDA = ServiceDefinition(service_name='mybusinessqanda', version='v1', discovery_service_url='https://mybusinessqanda.googleapis.com/$discovery/rest?version=v1')  # nopep8
  MYBUSINESSVERIFICATIONS = ServiceDefinition(service_name='mybusinessverifications', version='v1', discovery_service_url='https://mybusinessverifications.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NETAPP = ServiceDefinition(service_name='netapp', version='v1', discovery_service_url='https://netapp.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NETWORKCONNECTIVITY = ServiceDefinition(service_name='networkconnectivity', version='v1', discovery_service_url='https://networkconnectivity.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NETWORKMANAGEMENT = ServiceDefinition(service_name='networkmanagement', version='v1', discovery_service_url='https://networkmanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NETWORKSECURITY = ServiceDefinition(service_name='networksecurity', version='v1', discovery_service_url='https://networksecurity.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NETWORKSERVICES = ServiceDefinition(service_name='networkservices', version='v1', discovery_service_url='https://networkservices.googleapis.com/$discovery/rest?version=v1')  # nopep8
  NOTEBOOKS = ServiceDefinition(service_name='notebooks', version='v2', discovery_service_url='https://notebooks.googleapis.com/$discovery/rest?version=v2')  # nopep8
  OAUTH2 = ServiceDefinition(service_name='oauth2', version='v2', discovery_service_url='https://www.googleapis.com/discovery/v1/apis/oauth2/v2/rest')  # nopep8
  OBSERVABILITY = ServiceDefinition(service_name='observability', version='v1', discovery_service_url='https://observability.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ONDEMANDSCANNING = ServiceDefinition(service_name='ondemandscanning', version='v1', discovery_service_url='https://ondemandscanning.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ORACLEDATABASE = ServiceDefinition(service_name='oracledatabase', version='v1', discovery_service_url='https://oracledatabase.googleapis.com/$discovery/rest?version=v1')  # nopep8
  ORGPOLICY = ServiceDefinition(service_name='orgpolicy', version='v2', discovery_service_url='https://orgpolicy.googleapis.com/$discovery/rest?version=v2')  # nopep8
  OSCONFIG = ServiceDefinition(service_name='osconfig', version='v2', discovery_service_url='https://osconfig.googleapis.com/$discovery/rest?version=v2')  # nopep8
  OSLOGIN = ServiceDefinition(service_name='oslogin', version='v1', discovery_service_url='https://oslogin.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PAGESPEEDONLINE = ServiceDefinition(service_name='pagespeedonline', version='v5', discovery_service_url='https://pagespeedonline.googleapis.com/$discovery/rest?version=v5')  # nopep8
  PARALLELSTORE = ServiceDefinition(service_name='parallelstore', version='v1', discovery_service_url='https://parallelstore.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PARAMETERMANAGER = ServiceDefinition(service_name='parametermanager', version='v1', discovery_service_url='https://parametermanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PAYMENTSRESELLERSUBSCRIPTION = ServiceDefinition(service_name='paymentsresellersubscription', version='v1', discovery_service_url='https://paymentsresellersubscription.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PEOPLE = ServiceDefinition(service_name='people', version='v1', discovery_service_url='https://people.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PLACES = ServiceDefinition(service_name='places', version='v1', discovery_service_url='https://places.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PLAYCUSTOMAPP = ServiceDefinition(service_name='playcustomapp', version='v1', discovery_service_url='https://playcustomapp.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PLAYDEVELOPERREPORTING = ServiceDefinition(service_name='playdeveloperreporting', version='v1beta1', discovery_service_url='https://playdeveloperreporting.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  PLAYGROUPING = ServiceDefinition(service_name='playgrouping', version='v1alpha1', discovery_service_url='https://playgrouping.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  PLAYINTEGRITY = ServiceDefinition(service_name='playintegrity', version='v1', discovery_service_url='https://playintegrity.googleapis.com/$discovery/rest?version=v1')  # nopep8
  POLICYANALYZER = ServiceDefinition(service_name='policyanalyzer', version='v1', discovery_service_url='https://policyanalyzer.googleapis.com/$discovery/rest?version=v1')  # nopep8
  POLICYSIMULATOR = ServiceDefinition(service_name='policysimulator', version='v1', discovery_service_url='https://policysimulator.googleapis.com/$discovery/rest?version=v1')  # nopep8
  POLICYTROUBLESHOOTER = ServiceDefinition(service_name='policytroubleshooter', version='v3', discovery_service_url='https://policytroubleshooter.googleapis.com/$discovery/rest?version=v3')  # nopep8
  POLLEN = ServiceDefinition(service_name='pollen', version='v1', discovery_service_url='https://pollen.googleapis.com/$discovery/rest?version=v1')  # nopep8
  POLY = ServiceDefinition(service_name='poly', version='v1', discovery_service_url='https://poly.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PRIVATECA = ServiceDefinition(service_name='privateca', version='v1', discovery_service_url='https://privateca.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PROD_TT_SASPORTAL = ServiceDefinition(service_name='prod_tt_sasportal', version='v1alpha1', discovery_service_url='https://prod-tt-sasportal.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  PUBLICCA = ServiceDefinition(service_name='publicca', version='v1', discovery_service_url='https://publicca.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PUBSUB = ServiceDefinition(service_name='pubsub', version='v1', discovery_service_url='https://pubsub.googleapis.com/$discovery/rest?version=v1')  # nopep8
  PUBSUBLITE = ServiceDefinition(service_name='pubsublite', version='v1', discovery_service_url='https://pubsublite.googleapis.com/$discovery/rest?version=v1')  # nopep8
  RAPIDMIGRATIONASSESSMENT = ServiceDefinition(service_name='rapidmigrationassessment', version='v1', discovery_service_url='https://rapidmigrationassessment.googleapis.com/$discovery/rest?version=v1')  # nopep8
  READERREVENUESUBSCRIPTIONLINKING = ServiceDefinition(service_name='readerrevenuesubscriptionlinking', version='v1', discovery_service_url='https://readerrevenuesubscriptionlinking.googleapis.com/$discovery/rest?version=v1')  # nopep8
  REALTIMEBIDDING = ServiceDefinition(service_name='realtimebidding', version='v1', discovery_service_url='https://realtimebidding.googleapis.com/$discovery/rest?version=v1')  # nopep8
  RECAPTCHAENTERPRISE = ServiceDefinition(service_name='recaptchaenterprise', version='v1', discovery_service_url='https://recaptchaenterprise.googleapis.com/$discovery/rest?version=v1')  # nopep8
  RECOMMENDATIONENGINE = ServiceDefinition(service_name='recommendationengine', version='v1beta1', discovery_service_url='https://recommendationengine.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  RECOMMENDER = ServiceDefinition(service_name='recommender', version='v1', discovery_service_url='https://recommender.googleapis.com/$discovery/rest?version=v1')  # nopep8
  REDIS = ServiceDefinition(service_name='redis', version='v1', discovery_service_url='https://redis.googleapis.com/$discovery/rest?version=v1')  # nopep8
  RESELLER = ServiceDefinition(service_name='reseller', version='v1', discovery_service_url='https://reseller.googleapis.com/$discovery/rest?version=v1')  # nopep8
  RETAIL = ServiceDefinition(service_name='retail', version='v2', discovery_service_url='https://retail.googleapis.com/$discovery/rest?version=v2')  # nopep8
  RUN = ServiceDefinition(service_name='run', version='v2', discovery_service_url='https://run.googleapis.com/$discovery/rest?version=v2')  # nopep8
  RUNTIMECONFIG = ServiceDefinition(service_name='runtimeconfig', version='v1', discovery_service_url='https://runtimeconfig.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SAASSERVICEMGMT = ServiceDefinition(service_name='saasservicemgmt', version='v1beta1', discovery_service_url='https://saasservicemgmt.googleapis.com/$discovery/rest?version=v1beta1')  # nopep8
  SAFEBROWSING = ServiceDefinition(service_name='safebrowsing', version='v5', discovery_service_url='https://safebrowsing.googleapis.com/$discovery/rest?version=v5')  # nopep8
  SASPORTAL = ServiceDefinition(service_name='sasportal', version='v1alpha1', discovery_service_url='https://sasportal.googleapis.com/$discovery/rest?version=v1alpha1')  # nopep8
  SCRIPT = ServiceDefinition(service_name='script', version='v1', discovery_service_url='https://script.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SEARCHADS360 = ServiceDefinition(service_name='searchads360', version='v0', discovery_service_url='https://searchads360.googleapis.com/$discovery/rest?version=v0')  # nopep8
  SEARCHCONSOLE = ServiceDefinition(service_name='searchconsole', version='v1', discovery_service_url='https://searchconsole.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SECRETMANAGER = ServiceDefinition(service_name='secretmanager', version='v1', discovery_service_url='https://secretmanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SECURESOURCEMANAGER = ServiceDefinition(service_name='securesourcemanager', version='v1', discovery_service_url='https://securesourcemanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SECURITYCENTER = ServiceDefinition(service_name='securitycenter', version='v1', discovery_service_url='https://securitycenter.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SECURITYPOSTURE = ServiceDefinition(service_name='securityposture', version='v1', discovery_service_url='https://securityposture.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SERVICECONSUMERMANAGEMENT = ServiceDefinition(service_name='serviceconsumermanagement', version='v1', discovery_service_url='https://serviceconsumermanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SERVICECONTROL = ServiceDefinition(service_name='servicecontrol', version='v2', discovery_service_url='https://servicecontrol.googleapis.com/$discovery/rest?version=v2')  # nopep8
  SERVICEDIRECTORY = ServiceDefinition(service_name='servicedirectory', version='v1', discovery_service_url='https://servicedirectory.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SERVICEMANAGEMENT = ServiceDefinition(service_name='servicemanagement', version='v1', discovery_service_url='https://servicemanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SERVICENETWORKING = ServiceDefinition(service_name='servicenetworking', version='v1', discovery_service_url='https://servicenetworking.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SERVICEUSAGE = ServiceDefinition(service_name='serviceusage', version='v1', discovery_service_url='https://serviceusage.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SHEETS = ServiceDefinition(service_name='sheets', version='v4', discovery_service_url='https://sheets.googleapis.com/$discovery/rest?version=v4')  # nopep8
  SITEVERIFICATION = ServiceDefinition(service_name='siteVerification', version='v1', discovery_service_url='https://siteverification.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SLIDES = ServiceDefinition(service_name='slides', version='v1', discovery_service_url='https://slides.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SMARTDEVICEMANAGEMENT = ServiceDefinition(service_name='smartdevicemanagement', version='v1', discovery_service_url='https://smartdevicemanagement.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SOLAR = ServiceDefinition(service_name='solar', version='v1', discovery_service_url='https://solar.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SPANNER = ServiceDefinition(service_name='spanner', version='v1', discovery_service_url='https://spanner.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SPEECH = ServiceDefinition(service_name='speech', version='v1', discovery_service_url='https://speech.googleapis.com/$discovery/rest?version=v1')  # nopep8
  SQLADMIN = ServiceDefinition(service_name='sqladmin', version='v1', discovery_service_url='https://sqladmin.googleapis.com/$discovery/rest?version=v1')  # nopep8
  STORAGE = ServiceDefinition(service_name='storage', version='v1', discovery_service_url='https://storage.googleapis.com/$discovery/rest?version=v1')  # nopep8
  STORAGEBATCHOPERATIONS = ServiceDefinition(service_name='storagebatchoperations', version='v1', discovery_service_url='https://storagebatchoperations.googleapis.com/$discovery/rest?version=v1')  # nopep8
  STORAGETRANSFER = ServiceDefinition(service_name='storagetransfer', version='v1', discovery_service_url='https://storagetransfer.googleapis.com/$discovery/rest?version=v1')  # nopep8
  STREETVIEWPUBLISH = ServiceDefinition(service_name='streetviewpublish', version='v1', discovery_service_url='https://streetviewpublish.googleapis.com/$discovery/rest?version=v1')  # nopep8
  STS = ServiceDefinition(service_name='sts', version='v1', discovery_service_url='https://sts.googleapis.com/$discovery/rest?version=v1')  # nopep8
  TAGMANAGER = ServiceDefinition(service_name='tagmanager', version='v2', discovery_service_url='https://tagmanager.googleapis.com/$discovery/rest?version=v2')  # nopep8
  TASKS = ServiceDefinition(service_name='tasks', version='v1', discovery_service_url='https://tasks.googleapis.com/$discovery/rest?version=v1')  # nopep8
  TESTING = ServiceDefinition(service_name='testing', version='v1', discovery_service_url='https://testing.googleapis.com/$discovery/rest?version=v1')  # nopep8
  TEXTTOSPEECH = ServiceDefinition(service_name='texttospeech', version='v1', discovery_service_url='https://texttospeech.googleapis.com/$discovery/rest?version=v1')  # nopep8
  TOOLRESULTS = ServiceDefinition(service_name='toolresults', version='v1beta3', discovery_service_url='https://toolresults.googleapis.com/$discovery/rest?version=v1beta3')  # nopep8
  TPU = ServiceDefinition(service_name='tpu', version='v2', discovery_service_url='https://tpu.googleapis.com/$discovery/rest?version=v2')  # nopep8
  TRAFFICDIRECTOR = ServiceDefinition(service_name='trafficdirector', version='v3', discovery_service_url='https://trafficdirector.googleapis.com/$discovery/rest?version=v3')  # nopep8
  TRANSCODER = ServiceDefinition(service_name='transcoder', version='v1', discovery_service_url='https://transcoder.googleapis.com/$discovery/rest?version=v1')  # nopep8
  TRANSLATE = ServiceDefinition(service_name='translate', version='v3', discovery_service_url='https://translation.googleapis.com/$discovery/rest?version=v3')  # nopep8
  TRAVELIMPACTMODEL = ServiceDefinition(service_name='travelimpactmodel', version='v1', discovery_service_url='https://travelimpactmodel.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VAULT = ServiceDefinition(service_name='vault', version='v1', discovery_service_url='https://vault.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VERIFIEDACCESS = ServiceDefinition(service_name='verifiedaccess', version='v2', discovery_service_url='https://verifiedaccess.googleapis.com/$discovery/rest?version=v2')  # nopep8
  VERSIONHISTORY = ServiceDefinition(service_name='versionhistory', version='v1', discovery_service_url='https://versionhistory.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VIDEOINTELLIGENCE = ServiceDefinition(service_name='videointelligence', version='v1', discovery_service_url='https://videointelligence.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VISION = ServiceDefinition(service_name='vision', version='v1', discovery_service_url='https://vision.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VMMIGRATION = ServiceDefinition(service_name='vmmigration', version='v1', discovery_service_url='https://vmmigration.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VMWAREENGINE = ServiceDefinition(service_name='vmwareengine', version='v1', discovery_service_url='https://vmwareengine.googleapis.com/$discovery/rest?version=v1')  # nopep8
  VPCACCESS = ServiceDefinition(service_name='vpcaccess', version='v1', discovery_service_url='https://vpcaccess.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WALLETOBJECTS = ServiceDefinition(service_name='walletobjects', version='v1', discovery_service_url='https://walletobjects.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WEBFONTS = ServiceDefinition(service_name='webfonts', version='v1', discovery_service_url='https://webfonts.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WEBRISK = ServiceDefinition(service_name='webrisk', version='v1', discovery_service_url='https://webrisk.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WEBSECURITYSCANNER = ServiceDefinition(service_name='websecurityscanner', version='v1', discovery_service_url='https://websecurityscanner.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WORKFLOWEXECUTIONS = ServiceDefinition(service_name='workflowexecutions', version='v1', discovery_service_url='https://workflowexecutions.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WORKFLOWS = ServiceDefinition(service_name='workflows', version='v1', discovery_service_url='https://workflows.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WORKLOADMANAGER = ServiceDefinition(service_name='workloadmanager', version='v1', discovery_service_url='https://workloadmanager.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WORKSPACEEVENTS = ServiceDefinition(service_name='workspaceevents', version='v1', discovery_service_url='https://workspaceevents.googleapis.com/$discovery/rest?version=v1')  # nopep8
  WORKSTATIONS = ServiceDefinition(service_name='workstations', version='v1', discovery_service_url='https://workstations.googleapis.com/$discovery/rest?version=v1')  # nopep8
  YOUTUBE = ServiceDefinition(service_name='youtube', version='v3', discovery_service_url='https://youtube.googleapis.com/$discovery/rest?version=v3')  # nopep8
  YOUTUBEANALYTICS = ServiceDefinition(service_name='youtubeAnalytics', version='v2', discovery_service_url='https://youtubeanalytics.googleapis.com/$discovery/rest?version=v2')  # nopep8
  YOUTUBEREPORTING = ServiceDefinition(service_name='youtubereporting', version='v1', discovery_service_url='https://youtubereporting.googleapis.com/$discovery/rest?version=v1')  # nopep8
