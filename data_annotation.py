import cobra

model = cobra.io.read_sbml_model("Recon3D.xml")

# mapping = {}

# with open("reac_xref.tsv") as f:
#     for line in f:
#         # 🔥 skip comments
#         if line.startswith("#"):
#             continue

#         parts = line.strip().split("\t")

#         if len(parts) < 3:
#             continue

#         ref = parts[0]
#         mnx = parts[1]

#         if not mnx.startswith("MNXR"):
#             continue

#         if mnx not in mapping:
#             mapping[mnx] = {}

#         if ref.startswith("kegg:"):
#             mapping[mnx]["kegg.reaction"] = ref.replace("kegg:", "")
        
#         elif ref.startswith("ec-code:"):
#             mapping[mnx]["ec-code"] = ref.replace("ec-code:", "")
        
#         elif ref.startswith("rhea:"):
#             mapping[mnx]["rhea.reaction"] = ref.replace("rhea:", "")


# print(mapping.get("MNXR94734"))


print("Reactions:", len(model.reactions))


print("\nExample metabolite:")
met = model.metabolites[0]

print("ID:", met.id)
print("Name:", met.name)
print("Compartment:", met.compartment)
print("Annotation:", met.annotation)



print("\nExample gene:")
gene = model.genes[0]

print("ID:", gene.id)
print("Name:", gene.name)
print("Annotation:", gene.annotation)


def annotate_reaction(rxn):
    if rxn.annotation is None:
        rxn.annotation = {}
    
    ann = rxn.annotation

    # MetaNetX-based annotation
    if 'metanetx.reaction' in ann:
        mnx = ann['metanetx.reaction']
        
        ann.setdefault('annotation_source', 'MetaNetX')
        ann.setdefault('kegg.reaction', f"linked_to_{mnx}")
        ann.setdefault('ec-code', "unknown")
        ann.setdefault('rhea.reaction', "unknown")

    # Name-based rules
    name = rxn.name.lower()

    if "transport" in name:
        ann['sbo'] = 'SBO:0000655'   # overwrite is OK here

    if "dehydrogenase" in name:
        ann['ec-code'] = '1.x.x.x'

    if "kinase" in name:
        ann['ec-code'] = '2.7.x.x'

    if "isomerase" in name:
        ann['ec-code'] = '5.x.x.x'

def annotate_reaction(rxn):
    if rxn.annotation is None:
        rxn.annotation = {}

    ann = rxn.annotation

    if 'metanetx.reaction' in ann:
        mnx = ann['metanetx.reaction']

        ann['annotation_source'] = 'MetaNetX'

        if mnx in mapping:
            ann.update(mapping[mnx])   # 🔥 REAL DATA HERE
            ann['confidence'] = 'high'
        else:
            ann.setdefault('kegg.reaction', 'unknown')
            ann.setdefault('ec-code', 'unknown')
            ann.setdefault('rhea.reaction', 'unknown')
            ann['confidence'] = 'low'



# rxn = model.reactions[0]

# print("BEFORE:")
# print(rxn.annotation)

# annotate_reaction(rxn)

# print("AFTER:")
# print(rxn.annotation)


# for rxn in model.reactions:
#     annotate_reaction(rxn)


for rxn in model.reactions:
    if "dehydrogenase" in rxn.name.lower():
        print(rxn.id, rxn.annotation)
        break

print(mapping.get(rxn.annotation['metanetx.reaction']))