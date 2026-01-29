

from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, DateTime, func, Numeric, BLOB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DataEntityModule(Base):
    __tablename__ = 't_data_entity'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uri = Column(String(65535), nullable=True)  # TEXT 类型映射为 String，长度可调整
    m_uid = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    time_bucket_id = Column(Integer, nullable=False)
    source = Column(Integer, nullable=False)
    label = Column(String(32), nullable=True)  # CHAR(32) 映射为 String(32)
    content = Column(BLOB, nullable=False)
    content_size_bytes = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False,default=func.current_timestamp(), onupdate=func.current_timestamp())
    created_at = Column(DateTime, nullable=False,default=func.current_timestamp())

    def get_dict(self):
        """返回对象的属性作为字典"""
        return {
            "id": self.id,
            "uri": self.uri,
            "m_uid": self.m_uid,
            "datetime": self.datetime,
            "time_bucket_id": self.time_bucket_id,
            "source": self.source,
            "label": self.label,
            "content": self.content,
            "content_size_bytes": self.content_size_bytes
        }