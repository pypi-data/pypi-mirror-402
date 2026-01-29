from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class HTMetaDataModule(Base):
    __tablename__ = 't_hf_metadata'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uri = Column(String(65535), nullable=True,unique=True)  # TEXT 类型映射为 String，长度可调整
    m_uid = Column(Integer, nullable=False)
    source = Column(Integer, nullable=False)
    encoding_key = Column(String(65535), nullable=True)
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    def get_dict(self):
        """返回对象的属性作为字典"""
        return {
            "id": self.id,
            "uri": self.uri,
            "m_uid": self.m_uid,
            "source": self.source,
            "encoding_key": self.encoding_key,
            "updated_at":self.updated_at,
        }
