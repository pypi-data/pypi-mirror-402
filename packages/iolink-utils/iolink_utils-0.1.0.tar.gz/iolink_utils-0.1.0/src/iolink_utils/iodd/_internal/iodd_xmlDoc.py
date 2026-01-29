from typing import Tuple, Dict
import xml.etree.ElementTree as elTree
from datetime import date

from .iodd_documentInfo import DocumentInfo
from .iodd_identity import Identity, DeviceVariant
from .iodd_features import Features
from .iodd_physical_layer import PhysicalLayer
from .iodd_variableCollection import Variable

from iolink_utils.exceptions import UnsupportedComplexDataType, UnsupportedSimpleDataType
from iolink_utils.utils.version import Version
from iolink_utils.definitions.bitRate import BitRate
from iolink_utils.definitions.profiles import ProfileID
from iolink_utils.octetDecoder.octetDecoder import MSequenceCapability


class IoddXmlDoc:
    def __init__(self, ioddXmlFilePath: str):
        self._tree = elTree.parse(ioddXmlFilePath)
        self._root = self._tree.getroot()

        # namespaces
        self._namespaces = {
            'iolink': self._root.tag.split('}')[0].strip('{'),
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

        # local name of root
        self._docType = self._root.tag.split('}')[-1]

    @property
    def docType(self) -> str:
        return self._docType

    def getDocumentInfo(self) -> DocumentInfo:
        xmlDocumentInfo = self._root.find(".//iolink:DocumentInfo", self._namespaces)

        docInfo = DocumentInfo()
        if xmlDocumentInfo is not None:
            docInfo.version = Version(xmlDocumentInfo.get("version"))
            docInfo.releaseDate = date.fromisoformat(
                xmlDocumentInfo.get("releaseDate").strip()
            )
            docInfo.copyright = xmlDocumentInfo.get("copyright")

        return docInfo

    def getIdentity(self) -> Identity:
        xmlIdentity = self._root.find(".//iolink:DeviceIdentity", self._namespaces)
        identity = Identity()

        if xmlIdentity is not None:
            identity.vendorId = int(xmlIdentity.get("vendorId"))
            identity.deviceId = int(xmlIdentity.get("deviceId"))
            identity.vendorName = xmlIdentity.get("vendorName")

            identity.vendorText = self._getTextTuple(xmlIdentity, 'VendorText')
            identity.vendorUrl = self._getTextTuple(xmlIdentity, 'VendorUrl')

            xml_vendorLogo = xmlIdentity.find(".//iolink:VendorLogo", self._namespaces)
            identity.vendorLogo = "" if xml_vendorLogo is None else xml_vendorLogo.get('name')

            identity.deviceName = self._getTextTuple(xmlIdentity, 'DeviceName')
            identity.deviceFamily = self._getTextTuple(xmlIdentity, 'DeviceFamily')

            for xml_deviceVariant in xmlIdentity.findall(".//iolink:DeviceVariant", self._namespaces):
                variant = DeviceVariant()
                variant.productId = xml_deviceVariant.get('productId')
                variant.deviceSymbol = xml_deviceVariant.get('deviceSymbol')
                variant.deviceIcon = xml_deviceVariant.get('deviceIcon')
                variant.name = self._getTextTuple(xml_deviceVariant, 'Name')
                variant.description = self._getTextTuple(xml_deviceVariant, 'Description')
                identity.deviceVariants.append(variant)

        return identity

    def getDeviceFeatures(self) -> Features:
        xmlFeatures = self._root.find(".//iolink:Features", self._namespaces)
        features = Features()

        if xmlFeatures is not None:
            features.blockParameter = xmlFeatures.get("blockParameter") == "true"
            features.dataStorage = xmlFeatures.get("dataStorage") == "true"
            features.profileIDs = [
                ProfileID(int(c))
                for c in xmlFeatures.get("profileCharacteristic", "").split()
            ]

            xml_locks = xmlFeatures.find("iolink:SupportedAccessLocks", self._namespaces)
            if xml_locks is not None:
                features.supportedAccessLocks.parameter = xml_locks.get("parameter")
                features.supportedAccessLocks.dataStorage = xml_locks.get("dataStorage")
                features.supportedAccessLocks.localParameterization = xml_locks.get("localParameterization")
                features.supportedAccessLocks.localUserInterface = xml_locks.get("localUserInterface")

        return features

    def getPhysicalLayer(self) -> PhysicalLayer:
        xmlPhysicalLayer = self._root.find(".//iolink:PhysicalLayer", self._namespaces)
        physicalLayer = PhysicalLayer()

        if xmlPhysicalLayer is not None:
            bitrate = xmlPhysicalLayer.get("bitrate") or xmlPhysicalLayer.get("baudrate")
            physicalLayer.bitrate = BitRate(bitrate)
            physicalLayer.minCycleTime = int(xmlPhysicalLayer.get("minCycleTime"))
            physicalLayer.sioSupported = xmlPhysicalLayer.get("sioSupported") == "true"

            capa = xmlPhysicalLayer.get("mSequenceCapability")
            physicalLayer.mSequenceCapability = (
                MSequenceCapability(int(capa)) if capa else None
            )

        return physicalLayer

    def getVariableCollection(self) -> Dict[int, Variable]:
        variableCollection: Dict[int, Variable] = {}

        for xml_variable in self._root.findall(".//iolink:Variable", self._namespaces):
            variable = Variable()
            variable.id = xml_variable.get("id")
            variable.index = int(xml_variable.get("index"))
            variable.name = self._getTextForTextID(xml_variable.find('iolink:Name', self._namespaces).get('textId'))

            variableCollection[variable.index] = variable

        return variableCollection

    def getProcessDataDefinition(self):
        pdDefs = {}

        for xmlProcessData in self._root.findall(".//iolink:ProcessData", self._namespaces):
            xmlCond = xmlProcessData.find("iolink:Condition", self._namespaces)
            condition = None if xmlCond is None else int(xmlCond.get("value"))

            processData_json = {'id': xmlProcessData.get("id")}

            pdIn = xmlProcessData.find("iolink:ProcessDataIn", self._namespaces)
            if pdIn is not None:
                processData_json['pdIn'] = self._getProcessDataInOutAsJSON(pdIn)

            pdOut = xmlProcessData.find("iolink:ProcessDataOut", self._namespaces)
            if pdOut is not None:
                processData_json['pdOut'] = self._getProcessDataInOutAsJSON(pdOut)

            pdDefs[condition] = processData_json

        return pdDefs

    def _getTextTuple(self, xmlElement, textXmlTag: str) -> Tuple[str, str]:
        textTag = xmlElement.find(f'iolink:{textXmlTag}', self._namespaces)
        if textTag is not None:
            text_id = textTag.get('textId')
            return text_id, self._getTextForTextID(text_id)
        return "", ""

    def _getTextForTextID(self, textId: str, language: str = "en") -> str:
        for coll in self._root.findall(".//iolink:ExternalTextCollection", self._namespaces):
            for lang in coll.findall("iolink:PrimaryLanguage", self._namespaces):
                if lang.get(f"{{{self._namespaces['xml']}}}lang") == language:
                    for text in lang.findall("iolink:Text", self._namespaces):
                        if text.get("id") == textId:
                            return text.get("value", "")
        return ""

    def _getDatatype(self, xmlElement):
        for tag in ("Datatype", "SimpleDatatype", "DatatypeRef"):
            el = xmlElement.find(f"iolink:{tag}", self._namespaces)
            if el is not None:
                if tag == "DatatypeRef":
                    ref_id = el.get("datatypeId")
                    for dt in self._root.findall(".//iolink:Datatype", self._namespaces):
                        if dt.get("id") == ref_id:
                            return dt
                return el
        return None

    def _getProcessDataInOutAsJSON(self, xmlProcessData):
        textId = xmlProcessData.find('iolink:Name', self._namespaces).get('textId')
        dataType = self._getDatatype(xmlProcessData)

        return {
            "id": xmlProcessData.get("id"),
            "bitLength": int(xmlProcessData.get("bitLength")),
            "name": (textId, self._getTextForTextID(textId)),
            "dataFormat": self._getDatatypeAsJSON(dataType)
        }

    def _getDatatypeAsJSON(self, xmlDataType):
        xsiType = xmlDataType.get(f"{{{self._namespaces['xsi']}}}type")

        if xsiType in ('RecordT', 'ArrayT'):
            return self._getComplexDatatypeAsJSON(xmlDataType)

        return [{
            'bitOffset': 0,
            'data': self._getSimpleDatatypeAsJSON(xmlDataType)
        }]

    def _getComplexDatatypeAsJSON(self, xmlComplexDatatype):
        xsiType = xmlComplexDatatype.get(f"{{{self._namespaces['xsi']}}}type")

        if xsiType == 'RecordT':
            return self._getRecordTypeAsJSON(xmlComplexDatatype)
        if xsiType == 'ArrayT':
            return self._getArrayTypeAsJSON(xmlComplexDatatype)

        raise UnsupportedComplexDataType(f"Unsupported complex data type ({xsiType})")

    def _getRecordTypeAsJSON(self, xmlRecordDatatype):
        items = []

        for recordItem in xmlRecordDatatype.findall(".//iolink:RecordItem", self._namespaces):
            textId = recordItem.find('iolink:Name', self._namespaces).get('textId')
            dataType = self._getDatatype(recordItem)

            items.append({
                'bitOffset': int(recordItem.get("bitOffset")),
                'subIndex': int(recordItem.get("subindex")),
                'name': (textId, self._getTextForTextID(textId)),
                'data': self._getSimpleDatatypeAsJSON(dataType)
            })

        return items

    def _getArrayTypeAsJSON(self, xmlArrayDatatype):
        items = []
        count = int(xmlArrayDatatype.get('count'))

        dataType = self._getDatatype(xmlArrayDatatype)
        datatype_json = self._getSimpleDatatypeAsJSON(dataType)

        for i in range(count):
            items.append({
                'bitOffset': datatype_json['bitLength'] * i,
                'data': datatype_json
            })

        return items

    def _getSimpleDatatypeAsJSON(self, xmlSimpleDatatype):
        xsiType = xmlSimpleDatatype.get(f"{{{self._namespaces['xsi']}}}type")

        if xsiType == 'BooleanT':
            return {'type': bool, 'bitLength': 1}
        if xsiType in ('UIntegerT', 'IntegerT'):
            return {'type': int, 'bitLength': int(xmlSimpleDatatype.get("bitLength"))}
        if xsiType == 'Float32T':
            return {'type': float, 'bitLength': 32}
        if xsiType in ('StringT', 'OctetStringT'):
            return {
                'type': bytearray,
                'bitLength': int(xmlSimpleDatatype.get("fixedLength")) * 8
            }

        raise UnsupportedSimpleDataType(f"Not supported '{xsiType}'")
