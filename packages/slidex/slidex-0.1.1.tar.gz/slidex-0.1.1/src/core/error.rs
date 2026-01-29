use std::fmt;

#[derive(Debug)]
pub enum CoreError {
    NotImplemented(&'static str),
    Io(std::io::Error),
    Zip(zip::result::ZipError),
    XmlParse(quick_xml::Error),
    Xml(String),
    MissingPart(&'static str),
    InvalidPackage(&'static str),
}

impl fmt::Display for CoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CoreError::NotImplemented(feature) => write!(f, "Not implemented: {feature}"),
            CoreError::Io(err) => write!(f, "IO error: {err}"),
            CoreError::Zip(err) => write!(f, "Zip error: {err}"),
            CoreError::XmlParse(err) => write!(f, "XML error: {err}"),
            CoreError::Xml(err) => write!(f, "XML error: {err}"),
            CoreError::MissingPart(part) => write!(f, "Missing required part: {part}"),
            CoreError::InvalidPackage(msg) => write!(f, "Invalid package: {msg}"),
        }
    }
}

impl std::error::Error for CoreError {}

pub type Result<T> = std::result::Result<T, CoreError>;

impl From<std::io::Error> for CoreError {
    fn from(err: std::io::Error) -> Self {
        CoreError::Io(err)
    }
}

impl From<zip::result::ZipError> for CoreError {
    fn from(err: zip::result::ZipError) -> Self {
        CoreError::Zip(err)
    }
}

impl From<quick_xml::Error> for CoreError {
    fn from(err: quick_xml::Error) -> Self {
        CoreError::XmlParse(err)
    }
}
