import ifcopenshell


class LinkEntity(object):
    def __init__(self):
        self.ifc_entity = []

    def traverse_entity(self, ifc):
        for _ in ifc:
            if type(_) is ifcopenshell.entity_instance and _.id() != 0:
                self.find_all_entity(_)
                self.ifc_entity.append(_)
            elif type(_) is tuple:
                for v in _:
                    if type(v) is ifcopenshell.entity_instance and v.id() != 0:
                        self.find_all_entity(v)
                        self.ifc_entity.append(v)

    def find_all_entity(self,ifc):
        self.ifc_entity.append(ifc)
        for _ in ifc:
            if type(_) is ifcopenshell.entity_instance and _.id() != 0:
                self.ifc_entity.append(_)
                self.traverse_entity(_)
            elif type(_) is tuple:
                self.traverse_entity(_)
        return set(self.ifc_entity)


