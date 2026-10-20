"""SQLAlchemy tenant adapter; excludes deleted and cross-tenant endpoints."""
from bcms_domain.graph import build_graph
from app.models.process import Asset, BusinessProcess, Dependency


def tenant_graph(db, organization_id):
    def active(cls):
        return db.query(cls).filter(cls.organization_id == organization_id, cls.is_deleted == False)
    return build_graph([p.id for p in active(BusinessProcess)], [a.id for a in active(Asset)],
                       [dict(from_type=d.from_type, from_id=d.from_id, to_type=d.to_type, to_id=d.to_id) for d in active(Dependency)])
