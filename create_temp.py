import ifcopenshell
import extract_ifc as ext


def get_head(file_path):
    with open(file_path, 'r') as f:
        HEAD = []
        for _ in f.readlines():
            HEAD.append(_)
            if _ == 'ENDSEC;\n':
                break
        return HEAD


def get_project(ifc_agg):
    entity = []
    """
    write below two in write template
    ifc_file = ifcopenshell.open(path)
    ifc_agg = ifc_file.by_type('IFCRELAGGREGATES')
    """
    for _ in ifc_agg:
        entity.append(_[4])
        for v in _[5]:
            entity.append(v)
    cleaned_entity = list(set(entity))

    entity_for_template = []
    for _ in cleaned_entity:
        temp = list(ext.LinkEntity().find_all_entity(_))
        for _ in temp:
            entity_for_template.append(_)

    return list(set(entity_for_template))


def write_template(pre_path, create_path):
    with open(create_path, 'w', encoding='utf-8') as f:
        for _ in get_head(pre_path):
            f.write(str(_))
        f.write('\n')
        f.write('DATA;')
        f.write('\n')
        ifc_file = ifcopenshell.open(pre_path)
        ifc_agg = ifc_file.by_type('IFCRELAGGREGATES')
        for _ in ifc_agg:
            f.write(str(_).upper() + ';' + '\n')
        for _ in get_project(ifc_agg):
            _ = drop_rep(_)
            f.write(str(_).upper() + ';' + '\n')


# only for site for now
def drop_rep(entity):
    if entity.is_a() == 'IfcSite':
        ifc_id = entity.id()
        val = list(entity)
        val[6] = None
        for _ in val:
            index = val.index(_)
            if index == 0:
                val[0] = '\'{}\''.format(val[0])
            elif index == 8:
                val[8] = '.ELEMENT.'
            elif type(_) is ifcopenshell.entity_instance:
                val[index] = '#{}'.format(_.id())
            elif _ is None:
                val[index] = '$'
            elif type(_) is str:
                val[index] = '\'{}\''.format(val[index])
        ifc_site = '#{}=IfcSite({},{},{},{},{},{},{},{},{},{},{},{},{},{})'.format(ifc_id, val[0], val[1], val[2],
                                                                                   val[3], val[4], val[5], val[6],
                                                                                   val[7], val[8], val[9], val[10],
                                                                                   val[11], val[12], val[13])
        return ifc_site
    else:
        return entity


def split_by_connection(ifc_connection):
    """
    write below two in write template
    ifc_file = ifcopenshell.open(path)
    ifc_connection = ifc_file.by_type('IFCRELCONNECTSWITHREALIZINGELEMENTS')
    """
    relate_elements = []
    realizing_elements = []
    for _ in ifc_connection:
        relate_elements.append(_[5])
        relate_elements.append(_[6])
        realizing_elements.append(_[7][0])
    relate_elements = list(set(relate_elements))
    realizing_elements = list(set(realizing_elements))
    return relate_elements, realizing_elements


def create_element(ifc_element):
    element_value = []
    temp = list(ext.LinkEntity().find_all_entity(ifc_element))
    for _ in temp:
        element_value.append(_)
    return element_value


def create_single_component(pre_file_path, folder_path):
    ifc_file = ifcopenshell.open(pre_file_path)
    ifc_connection = ifc_file.by_type('IFCRELCONNECTSWITHREALIZINGELEMENTS')
    sorted_types = split_by_connection(ifc_connection)
    for elements in sorted_types:
        for _ in elements:
            element_path = folder_path + '\\{}.ifc'.format(_.GlobalId)
            with open(element_path, 'w', encoding='utf-8') as f:
                for head in get_head(pre_file_path):
                    f.write(str(head))
                f.write('\n')
                f.write('DATA;')
                f.write('\n')
                ifc_agg = ifc_file.by_type('IFCRELAGGREGATES')
                for agg in ifc_agg:
                    f.write(str(agg).upper() + ';' + '\n')
                for tem in get_project(ifc_agg):
                    tem = drop_rep(tem)
                    f.write(str(tem).upper() + ';' + '\n')
                ifc_contain = ifc_file.by_type('IFCRELCONTAINEDINSPATIALSTRUCTURE')
                for contain in ifc_contain:
                    f.write(str(contain).upper() + ';' + '\n')
                print('element is: ', _)
                # print(create_element(_))
                element_value = []
                temp = list(ext.LinkEntity().find_all_entity(_))
                for _ in temp:
                    element_value.append(_)
                for element in element_value:
                    element = drop_rep(element)
                    f.write(str(element).upper() + ';' + '\n')
                f.write('\n')
                f.write('ENDSEC;')
                f.write('\n')
                f.write('END-ISO-10303-21;')

