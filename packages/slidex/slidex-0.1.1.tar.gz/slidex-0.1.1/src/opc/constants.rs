//! Constant values related to the Open Packaging Convention (OPC).
//!
//! These include content (MIME) types, relationship types, and namespaces.

pub mod content_type {
    //! Content type URIs (like MIME-types) that specify a part's format.

    pub const ASF: &str = "video/x-ms-asf";
    pub const AVI: &str = "video/avi";
    pub const BMP: &str = "image/bmp";
    pub const DML_CHART: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.chart+xml";
    pub const DML_CHARTSHAPES: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.chartshapes+xml";
    pub const DML_DIAGRAM_COLORS: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.diagramColors+xml";
    pub const DML_DIAGRAM_DATA: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml";
    pub const DML_DIAGRAM_DRAWING: &str =
        "application/vnd.ms-office.drawingml.diagramDrawing+xml";
    pub const DML_DIAGRAM_LAYOUT: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.diagramLayout+xml";
    pub const DML_DIAGRAM_STYLE: &str =
        "application/vnd.openxmlformats-officedocument.drawingml.diagramStyle+xml";
    pub const GIF: &str = "image/gif";
    pub const INK: &str = "application/inkml+xml";
    pub const JPEG: &str = "image/jpeg";
    pub const MOV: &str = "video/quicktime";
    pub const MP4: &str = "video/mp4";
    pub const MPG: &str = "video/mpeg";
    pub const MS_PHOTO: &str = "image/vnd.ms-photo";
    pub const MS_VIDEO: &str = "video/msvideo";
    pub const OFC_CHART_COLORS: &str = "application/vnd.ms-office.chartcolorstyle+xml";
    pub const OFC_CHART_EX: &str = "application/vnd.ms-office.chartex+xml";
    pub const OFC_CHART_STYLE: &str = "application/vnd.ms-office.chartstyle+xml";
    pub const OFC_CUSTOM_PROPERTIES: &str =
        "application/vnd.openxmlformats-officedocument.custom-properties+xml";
    pub const OFC_CUSTOM_XML_PROPERTIES: &str =
        "application/vnd.openxmlformats-officedocument.customXmlProperties+xml";
    pub const OFC_DRAWING: &str = "application/vnd.openxmlformats-officedocument.drawing+xml";
    pub const OFC_EXTENDED_PROPERTIES: &str =
        "application/vnd.openxmlformats-officedocument.extended-properties+xml";
    pub const OFC_OLE_OBJECT: &str = "application/vnd.openxmlformats-officedocument.oleObject";
    pub const OFC_PACKAGE: &str = "application/vnd.openxmlformats-officedocument.package";
    pub const OFC_THEME: &str = "application/vnd.openxmlformats-officedocument.theme+xml";
    pub const OFC_THEME_OVERRIDE: &str =
        "application/vnd.openxmlformats-officedocument.themeOverride+xml";
    pub const OFC_VML_DRAWING: &str =
        "application/vnd.openxmlformats-officedocument.vmlDrawing";
    pub const OPC_CORE_PROPERTIES: &str =
        "application/vnd.openxmlformats-package.core-properties+xml";
    pub const OPC_DIGITAL_SIGNATURE_CERTIFICATE: &str =
        "application/vnd.openxmlformats-package.digital-signature-certificate";
    pub const OPC_DIGITAL_SIGNATURE_ORIGIN: &str =
        "application/vnd.openxmlformats-package.digital-signature-origin";
    pub const OPC_DIGITAL_SIGNATURE_XMLSIGNATURE: &str =
        "application/vnd.openxmlformats-package.digital-signature-xmlsignature+xml";
    pub const OPC_RELATIONSHIPS: &str =
        "application/vnd.openxmlformats-package.relationships+xml";
    pub const PML_COMMENTS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.comments+xml";
    pub const PML_COMMENT_AUTHORS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml";
    pub const PML_HANDOUT_MASTER: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.handoutMaster+xml";
    pub const PML_NOTES_MASTER: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml";
    pub const PML_NOTES_SLIDE: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml";
    pub const PML_PRESENTATION: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.presentation";
    pub const PML_PRESENTATION_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml";
    pub const PML_PRES_MACRO_MAIN: &str =
        "application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml";
    pub const PML_PRES_PROPS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.presProps+xml";
    pub const PML_PRINTER_SETTINGS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.printerSettings";
    pub const PML_SLIDE: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.slide+xml";
    pub const PML_SLIDESHOW_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.slideshow.main+xml";
    pub const PML_SLIDE_LAYOUT: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml";
    pub const PML_SLIDE_MASTER: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml";
    pub const PML_SLIDE_UPDATE_INFO: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.slideUpdateInfo+xml";
    pub const PML_TABLE_STYLES: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml";
    pub const PML_TAGS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.tags+xml";
    pub const PML_TEMPLATE_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.template.main+xml";
    pub const PML_VIEW_PROPS: &str =
        "application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml";
    pub const PNG: &str = "image/png";
    pub const SML_CALC_CHAIN: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml";
    pub const SML_CHARTSHEET: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.chartsheet+xml";
    pub const SML_COMMENTS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml";
    pub const SML_CONNECTIONS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.connections+xml";
    pub const SML_CUSTOM_PROPERTY: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.customProperty";
    pub const SML_DIALOGSHEET: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.dialogsheet+xml";
    pub const SML_EXTERNAL_LINK: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.externalLink+xml";
    pub const SML_PIVOT_CACHE_DEFINITION: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml";
    pub const SML_PIVOT_CACHE_RECORDS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheRecords+xml";
    pub const SML_PIVOT_TABLE: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.pivotTable+xml";
    pub const SML_PRINTER_SETTINGS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.printerSettings";
    pub const SML_QUERY_TABLE: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.queryTable+xml";
    pub const SML_REVISION_HEADERS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.revisionHeaders+xml";
    pub const SML_REVISION_LOG: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.revisionLog+xml";
    pub const SML_SHARED_STRINGS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml";
    pub const SML_SHEET: &str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    pub const SML_SHEET_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml";
    pub const SML_SHEET_METADATA: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml";
    pub const SML_STYLES: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml";
    pub const SML_TABLE: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml";
    pub const SML_TABLE_SINGLE_CELLS: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.tableSingleCells+xml";
    pub const SML_TEMPLATE_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.template.main+xml";
    pub const SML_USER_NAMES: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.userNames+xml";
    pub const SML_VOLATILE_DEPENDENCIES: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.volatileDependencies+xml";
    pub const SML_WORKSHEET: &str =
        "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml";
    pub const SWF: &str = "application/x-shockwave-flash";
    pub const TIFF: &str = "image/tiff";
    pub const VIDEO: &str = "video/unknown";
    pub const WML_COMMENTS: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml";
    pub const WML_DOCUMENT: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    pub const WML_DOCUMENT_GLOSSARY: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.glossary+xml";
    pub const WML_DOCUMENT_MAIN: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml";
    pub const WML_ENDNOTES: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml";
    pub const WML_FONT_TABLE: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml";
    pub const WML_FOOTER: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml";
    pub const WML_FOOTNOTES: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml";
    pub const WML_HEADER: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml";
    pub const WML_NUMBERING: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml";
    pub const WML_PRINTER_SETTINGS: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.printerSettings";
    pub const WML_SETTINGS: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml";
    pub const WML_STYLES: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml";
    pub const WML_WEB_SETTINGS: &str =
        "application/vnd.openxmlformats-officedocument.wordprocessingml.webSettings+xml";
    pub const WMV: &str = "video/x-ms-wmv";
    pub const XML: &str = "application/xml";
    pub const X_EMF: &str = "image/x-emf";
    pub const X_FONTDATA: &str = "application/x-fontdata";
    pub const X_FONT_TTF: &str = "application/x-font-ttf";
    pub const X_MS_VIDEO: &str = "video/x-msvideo";
    pub const X_WMF: &str = "image/x-wmf";
}

pub mod namespace {
    //! Constant values for OPC XML namespaces.

    pub const DML_WORDPROCESSING_DRAWING: &str =
        "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing";
    pub const OFC_RELATIONSHIPS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
    pub const OPC_RELATIONSHIPS: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships";
    pub const OPC_CONTENT_TYPES: &str =
        "http://schemas.openxmlformats.org/package/2006/content-types";
    pub const WML_MAIN: &str = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
}

pub mod relationship_target_mode {
    //! Open XML relationship target modes.

    pub const EXTERNAL: &str = "External";
    pub const INTERNAL: &str = "Internal";
}

pub mod relationship_type {
    //! Relationship type URIs.

    pub const AUDIO: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio";
    pub const A_F_CHUNK: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/aFChunk";
    pub const CALC_CHAIN: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/calcChain";
    pub const CERTIFICATE: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships/digital-signature/certificate";
    pub const CHART: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart";
    pub const CHARTSHEET: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chartsheet";
    pub const CHART_COLOR_STYLE: &str =
        "http://schemas.microsoft.com/office/2011/relationships/chartColorStyle";
    pub const CHART_USER_SHAPES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chartUserShapes";
    pub const COMMENTS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments";
    pub const COMMENT_AUTHORS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/commentAuthors";
    pub const CONNECTIONS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/connections";
    pub const CONTROL: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/control";
    pub const CORE_PROPERTIES: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties";
    pub const CUSTOM_PROPERTIES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties";
    pub const CUSTOM_PROPERTY: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customProperty";
    pub const CUSTOM_XML: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXml";
    pub const CUSTOM_XML_PROPS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/customXmlProps";
    pub const DIAGRAM_COLORS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramColors";
    pub const DIAGRAM_DATA: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData";
    pub const DIAGRAM_LAYOUT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramLayout";
    pub const DIAGRAM_QUICK_STYLE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramQuickStyle";
    pub const DIALOGSHEET: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/dialogsheet";
    pub const DRAWING: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing";
    pub const ENDNOTES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes";
    pub const EXTENDED_PROPERTIES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties";
    pub const EXTERNAL_LINK: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink";
    pub const FONT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font";
    pub const FONT_TABLE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable";
    pub const FOOTER: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer";
    pub const FOOTNOTES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes";
    pub const GLOSSARY_DOCUMENT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/glossaryDocument";
    pub const HANDOUT_MASTER: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/handoutMaster";
    pub const HEADER: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header";
    pub const HYPERLINK: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink";
    pub const IMAGE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image";
    pub const MEDIA: &str = "http://schemas.microsoft.com/office/2007/relationships/media";
    pub const NOTES_MASTER: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster";
    pub const NOTES_SLIDE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide";
    pub const NUMBERING: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering";
    pub const OFFICE_DOCUMENT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument";
    pub const OLE_OBJECT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject";
    pub const ORIGIN: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships/digital-signature/origin";
    pub const PACKAGE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package";
    pub const PIVOT_CACHE_DEFINITION: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/pivotCacheDefinition";
    pub const PIVOT_CACHE_RECORDS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/spreadsheetml/pivotCacheRecords";
    pub const PIVOT_TABLE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/pivotTable";
    pub const PRES_PROPS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps";
    pub const PRINTER_SETTINGS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/printerSettings";
    pub const QUERY_TABLE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/queryTable";
    pub const REVISION_HEADERS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/revisionHeaders";
    pub const REVISION_LOG: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/revisionLog";
    pub const SETTINGS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings";
    pub const SHARED_STRINGS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings";
    pub const SHEET_METADATA: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata";
    pub const SIGNATURE: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships/digital-signature/signature";
    pub const SLIDE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide";
    pub const SLIDE_LAYOUT: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout";
    pub const SLIDE_MASTER: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster";
    pub const SLIDE_UPDATE_INFO: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideUpdateInfo";
    pub const STYLES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles";
    pub const TABLE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/table";
    pub const TABLE_SINGLE_CELLS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableSingleCells";
    pub const TABLE_STYLES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles";
    pub const TAGS: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/tags";
    pub const THEME: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme";
    pub const THEME_OVERRIDE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/themeOverride";
    pub const THUMBNAIL: &str =
        "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail";
    pub const USERNAMES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/usernames";
    pub const VIDEO: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/video";
    pub const VIEW_PROPS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps";
    pub const VML_DRAWING: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing";
    pub const VOLATILE_DEPENDENCIES: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/volatileDependencies";
    pub const WEB_SETTINGS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/webSettings";
    pub const WORKSHEET_SOURCE: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheetSource";
    pub const XML_MAPS: &str =
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/xmlMaps";
}
