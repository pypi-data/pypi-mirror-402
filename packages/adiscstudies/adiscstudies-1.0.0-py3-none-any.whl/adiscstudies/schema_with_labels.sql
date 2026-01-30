
CREATE TABLE IF NOT EXISTS "Study" (
    "Study specifier" VARCHAR(512) PRIMARY KEY,
    "Institution" VARCHAR(512)
);
COMMENT ON TABLE "Study" IS 'A planned process that consists of parts: planning, study design execution, documentation and which produce conclusion(s). (OBI:0000066)';
COMMENT ON COLUMN "Study"."Study specifier" IS 'A short name for the study meant mainly for human-readable reference which disambiguates against other studies in the context of a single database instance.';
COMMENT ON COLUMN "Study"."Institution" IS 'The primary institution in which the investigation is carried out, which provides resources for the investigation, or which directs the conduct of the investigation. (OBI:0000828)';

CREATE TABLE IF NOT EXISTS "Research professional" (
    "Full name" VARCHAR(512) PRIMARY KEY,
    "Surname" VARCHAR(512),
    "Given name" VARCHAR(512),
    "ORCID" VARCHAR(512)
);
COMMENT ON TABLE "Research professional" IS 'A person who performs research or a service that directly supports a research activity. (OBI:0000202)';
COMMENT ON COLUMN "Research professional"."Full name" IS 'A full set of all personal names by which an individual is known and that can be recited as a word-group, with the understanding that, taken together, they all relate to that one individual. (GSSO:001755)';
COMMENT ON COLUMN "Research professional"."Surname" IS 'An identifier that is typically a part of a persons name which has been passed, according to law or custom, from one or both parents to their children. (IAO:0020017)';
COMMENT ON COLUMN "Research professional"."Given name" IS 'A personal name that specifies and differentiates between members of a group of individuals, especially in a family, all of whose members usually share the same family name (surname). A given name is purposefully given, usually by a childs parents at or near birth, in contrast to an inherited one such as a family name. (IAO:0020016)';
COMMENT ON COLUMN "Research professional"."ORCID" IS 'A centrally registered identifier that is issued by ORCID (https://orcid.org/) and used to persistently identify oneself as a human researcher or contributor. (IAO:0000708)';

CREATE TABLE IF NOT EXISTS "Study contact person" (
    "Name" VARCHAR(512) REFERENCES "Research professional"("Full name") ON DELETE CASCADE ,
    "Study" VARCHAR(512) REFERENCES "Study"("Study specifier") ON DELETE CASCADE ,
    "Contact reference" VARCHAR(512)
);
COMMENT ON TABLE "Study contact person" IS 'A person who has responsibility for receiving general queries regarding the conduct of a given study. (NCIT:C25461)';
COMMENT ON COLUMN "Study contact person"."Name" IS 'A person who performs research or a service that directly supports a research activity. (OBI:0000202)';
COMMENT ON COLUMN "Study contact person"."Study" IS 'A planned process that consists of parts: planning, study design execution, documentation and which produce conclusion(s). (OBI:0000066)';
COMMENT ON COLUMN "Study contact person"."Contact reference" IS 'An address for direction of communication, e.g. an email address, a mailing address, or a phone number. (NCIT:C70806)';

CREATE TABLE IF NOT EXISTS "Study component" (
    "Primary study" VARCHAR(512),
    "Component study" VARCHAR(512)
);
COMMENT ON TABLE "Study component" IS 'A relation between a primary study and another study in which the latter is a component or part of the primary study. (BFO:0000050)';
COMMENT ON COLUMN "Study component"."Primary study" IS 'The primary study of the component relation.';
COMMENT ON COLUMN "Study component"."Component study" IS 'The component study of the component relation.';

CREATE TABLE IF NOT EXISTS "Publication" (
    "Title" VARCHAR(512) PRIMARY KEY,
    "Study" VARCHAR(512) REFERENCES "Study"("Study specifier") ON DELETE CASCADE ,
    "Document type" VARCHAR(512),
    "Publisher" VARCHAR(512),
    "Date of publication" VARCHAR(512),
    "Internet reference" VARCHAR
);
COMMENT ON TABLE "Publication" IS 'A document, i.e. a collection of information content entities intended to be understood together as a whole, which is the output of a publishing process and which is about an investigation. (IAO:0000312)';
COMMENT ON COLUMN "Publication"."Title" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';
COMMENT ON COLUMN "Publication"."Study" IS 'A planned process that consists of parts: planning, study design execution, documentation and which produce conclusion(s). (OBI:0000066)';
COMMENT ON COLUMN "Publication"."Document type" IS 'See IAO. (IAO:0000310)';
COMMENT ON COLUMN "Publication"."Publisher" IS 'The institution or organization which performs publication processes resulting in publications, i.e. which receives, accepts, and disseminates the document comprising the publications. (SIO:000885)';
COMMENT ON COLUMN "Publication"."Date of publication" IS 'The date on which the publication process was completed.';
COMMENT ON COLUMN "Publication"."Internet reference" IS 'A reference, typically a URL and often a DOI-formatted URL, that is issued by the publisher and refers to an at least partial digital representation of the publication. (SIO:000811)';

CREATE TABLE IF NOT EXISTS "Author" (
    "Person" VARCHAR(512) REFERENCES "Research professional"("Full name") ON DELETE CASCADE ,
    "Publication" VARCHAR(512) REFERENCES "Publication"("Title") ON DELETE CASCADE ,
    "Ordinality" VARCHAR(512)
);
COMMENT ON TABLE "Author" IS 'A person who performed a substantial amount of the writing of a given publication, or otherwise performed investigation and related work responsible for the substance of the publication. (IAO:0000442)';
COMMENT ON COLUMN "Author"."Person" IS 'A person who performs research or a service that directly supports a research activity. (OBI:0000202)';
COMMENT ON COLUMN "Author"."Publication" IS 'A document, i.e. a collection of information content entities intended to be understood together as a whole, which is the output of a publishing process and which is about an investigation. (IAO:0000312)';
COMMENT ON COLUMN "Author"."Ordinality" IS 'The position of an author in the rank order of authors advertised by the publisher of a given publication, typically decided by the authors as an indication of level of contribution, but sometimes decided by other means (e.g. alphabetical order on names). Often the author in first position declare responsibility for communication regarding the work.';

CREATE TABLE IF NOT EXISTS "Subject" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Species" VARCHAR(512),
    "Sex" VARCHAR(512),
    "Birth date" VARCHAR(512),
    "Death date" VARCHAR(512),
    "Cause of death" VARCHAR
);
COMMENT ON TABLE "Subject" IS 'A person, other organism, or biospecimen which is the subject of some study. (OBI:0000097)';
COMMENT ON COLUMN "Subject"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Subject"."Species" IS 'A collection of organisms whose members are related by a sequence of tokogenies (ancestry/descent), and for which the collection is maximal subject to the constraint it that does not span any speciation boundaries, i.e. temporal boundaries formed by allopatric, parapatric, or sympatric speciation events (Wheeler and Meier, Species Concepts and Phylogenetic Theory). For example, Homo sapiens (humans), or Mus musculus (mice).';
COMMENT ON COLUMN "Subject"."Sex" IS 'The class of reproductive compatibility to which a given organism belongs, in case its biological species admits such classes (gonochoric species). As indicated by observable phenotypic information. For example, male, female, or intersex. (PATO:0000047)';
COMMENT ON COLUMN "Subject"."Birth date" IS 'The date of inception, in the case of a biological subject. (UBERON:0035946)';
COMMENT ON COLUMN "Subject"."Death date" IS 'The date of conclusion, in the case of a biological subject. (UBERON:0035944)';
COMMENT ON COLUMN "Subject"."Cause of death" IS 'The most significant causative factor in the death of a given subject. Often but not always pertinent to the study of which the subject is a part, in the case of disease studies. (OPMI:0000543)';

CREATE TABLE IF NOT EXISTS "Diagnosis" (
    "Subject" VARCHAR(512) REFERENCES "Subject"("Identifier") ON DELETE CASCADE ,
    "Condition" VARCHAR(512),
    "Result" VARCHAR(512),
    "Assessor" VARCHAR(512),
    "Date" VARCHAR(512),
    "Date of evidence" VARCHAR(512)
);
COMMENT ON TABLE "Diagnosis" IS 'The concluding event of an assessors determination of the presence or absence of a specific condition in a subject. Often the determination is made on the basis of consideration of multiple factors. (OGMS:0000073)';
COMMENT ON COLUMN "Diagnosis"."Subject" IS 'A person, other organism, or biospecimen which is the subject of some study. (OBI:0000097)';
COMMENT ON COLUMN "Diagnosis"."Condition" IS 'The condition considered during a process of diagnosis. (BFO:0000016)';
COMMENT ON COLUMN "Diagnosis"."Result" IS 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer). (OGMS:0000073)';
COMMENT ON COLUMN "Diagnosis"."Assessor" IS 'The person or agent who performs a given diagnosis. (NCIT:C48206)';
COMMENT ON COLUMN "Diagnosis"."Date" IS 'The date on which a diagnosis was made. (NCIT:C164339)';
COMMENT ON COLUMN "Diagnosis"."Date of evidence" IS 'For an evaluation of activity or condition based on evidential factors of consideration, the most recent known date of creation of the evidence. If this date is accurately known, events after this date cannot bias the evaluation. For example, for a diagnosis based on a blood sample, X-rays, and a biopsy, if the blood sample was taken last, then the date of this sample is the maximal date of evidence.';

CREATE TABLE IF NOT EXISTS "Diagnostic selection criterion" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Condition" VARCHAR(512),
    "Result" VARCHAR(512)
);
COMMENT ON TABLE "Diagnostic selection criterion" IS 'A criterion for cohort selection on the basis of a diagnosis result. (OBI:0001755)';
COMMENT ON COLUMN "Diagnostic selection criterion"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Diagnostic selection criterion"."Condition" IS 'An an-principle empirically diagnosable condition of a subject. (BFO:0000016)';
COMMENT ON COLUMN "Diagnostic selection criterion"."Result" IS 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer). (OGMS:0000073)';

CREATE TABLE IF NOT EXISTS "Intervention" (
    "Subject" VARCHAR(512) REFERENCES "Subject"("Identifier") ON DELETE CASCADE ,
    "Specifier" VARCHAR(512),
    "Date" VARCHAR(512)
);
COMMENT ON TABLE "Intervention" IS 'An activity that produces an effect, or that is intended to alter the course of a disease in a patient. (NCIT:C25218)';
COMMENT ON COLUMN "Intervention"."Subject" IS 'A person, other organism, or biospecimen which is the subject of some study. (OBI:0000097)';
COMMENT ON COLUMN "Intervention"."Specifier" IS 'An identifier meant to be used in a limited context, for disambiguation between highly salient alternatives.';
COMMENT ON COLUMN "Intervention"."Date" IS 'The date that a specific intervention was performed. (NCIT:C80454)';

CREATE TABLE IF NOT EXISTS "Specimen collection study" (
    "Name" VARCHAR(512) PRIMARY KEY,
    "Extraction method" VARCHAR(512),
    "Preservation method" VARCHAR(512),
    "Storage location" VARCHAR,
    "Inception date" VARCHAR(512),
    "Conclusion date" VARCHAR(512)
);
COMMENT ON TABLE "Specimen collection study" IS 'An effort, generally undertaken by a group of collaborating participants, to collect biospecimens of a particular type for the purpose of eventual observation/measurement and analysis. Typically initiated and concluded at specific times, but may be ongoing. (OBI:0000471)';
COMMENT ON COLUMN "Specimen collection study"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';
COMMENT ON COLUMN "Specimen collection study"."Extraction method" IS 'The method by which subspecimens are extracted from a source specimen. For example, fine-needle aspiration. (OBI:0001882)';
COMMENT ON COLUMN "Specimen collection study"."Preservation method" IS 'A method of treatment of a biospecimen intended to preserve the structure and chemical composition which were present at the time immediately prior to extraction. (NCIT:C64262)';
COMMENT ON COLUMN "Specimen collection study"."Storage location" IS 'The location of storage of biospecimens during the period after collection but before measurement or analysis. (OBI:0302893)';
COMMENT ON COLUMN "Specimen collection study"."Inception date" IS 'The initial date of the continuants existence. (NCIT:C68616)';
COMMENT ON COLUMN "Specimen collection study"."Conclusion date" IS 'The final date of the continuants existence. (NCIT:C68617)';

CREATE TABLE IF NOT EXISTS "Specimen collection process" (
    "Specimen" VARCHAR(512) PRIMARY KEY,
    "Source" VARCHAR(512),
    "Source site" VARCHAR,
    "Source age" VARCHAR,
    "Extraction date" VARCHAR(512),
    "Study" VARCHAR(512) REFERENCES "Specimen collection study"("Name") ON DELETE CASCADE 
);
COMMENT ON TABLE "Specimen collection process" IS 'A process in which a biospecimen is retrieved from its natural environment or host and placed under control for observation and analysis. Typically the process consists of extraction of a subspecimen from a whole organism, or from another subspecimen, at a specific site, preservation using a specific protocol, and storage together with similar specimens collected as part of a study. (OBI:0000659)';
COMMENT ON COLUMN "Specimen collection process"."Specimen" IS 'The subspecimen extracted during a given biospecimen collection process.';
COMMENT ON COLUMN "Specimen collection process"."Source" IS 'The biospecimen from which a subspecimen was extracted during the given specimen collection process.';
COMMENT ON COLUMN "Specimen collection process"."Source site" IS 'The location on the source specimen from which a subspecimen is extracted. (BFO:0000029)';
COMMENT ON COLUMN "Specimen collection process"."Source age" IS 'The amount of time between the inception of a given biospecimen (typically extraction) and the given event. Typically denominated in number of days. (PATO:0000011)';
COMMENT ON COLUMN "Specimen collection process"."Extraction date" IS 'The time at which something happens. When represented by a string, the preferred format is ISO 8601-1:2019 (e.g. 1999-04-01 for April 1st in the year 1999), but this can also be represented as a timestamp or even a relative, ordinal value, so long as it is consistent across related records.';
COMMENT ON COLUMN "Specimen collection process"."Study" IS 'An effort, generally undertaken by a group of collaborating participants, to collect biospecimens of a particular type for the purpose of eventual observation/measurement and analysis. Typically initiated and concluded at specific times, but may be ongoing. (OBI:0000471)';

CREATE TABLE IF NOT EXISTS "Histology assessment process" (
    "Slide" VARCHAR(512) REFERENCES "Specimen collection process"("Specimen") ON DELETE CASCADE ,
    "Assay" VARCHAR(512),
    "Result" VARCHAR(512),
    "Assessor" VARCHAR,
    "Assessment date" VARCHAR(512)
);
COMMENT ON TABLE "Histology assessment process" IS 'A specific instance of performance of an histology assay by an assessor at a specific time. (OBI:0600020)';
COMMENT ON COLUMN "Histology assessment process"."Slide" IS 'A biological specimen together with a supporting substrate on which it is mounted. Typically for the purpose of microscopy analysis. (OBI:0400170)';
COMMENT ON COLUMN "Histology assessment process"."Assay" IS 'The assessment (e.g. of a histology slide) for a specific feature. For example, tumor grading. (OBI:0001896)';
COMMENT ON COLUMN "Histology assessment process"."Result" IS 'The empirical claim about a subject supported by an assay analyzing that subject. When the assay type is binary (present or not present), the assay result is just assertion or non-assertion of the claim corresponding to the assay type (for example, an assay for the presence of a specific disease). In this case a common convention for the values is positive or negative. (OBI:0001909)';
COMMENT ON COLUMN "Histology assessment process"."Assessor" IS 'The person or agent who performs a given assay. (OBI:0001950)';
COMMENT ON COLUMN "Histology assessment process"."Assessment date" IS 'The time at which something happens. When represented by a string, the preferred format is ISO 8601-1:2019 (e.g. 1999-04-01 for April 1st in the year 1999), but this can also be represented as a timestamp or even a relative, ordinal value, so long as it is consistent across related records.';

CREATE TABLE IF NOT EXISTS "Specimen measurement study" (
    "Name" VARCHAR(512) PRIMARY KEY,
    "Assay" VARCHAR(512),
    "Machine" VARCHAR(512),
    "Software" VARCHAR(512),
    "Inception date" VARCHAR(512),
    "Conclusion date" VARCHAR(512)
);
COMMENT ON TABLE "Specimen measurement study" IS 'An effort, generally undertaken by a group of collaborating participants, to make data measurements on a collection of biological specimens. Typically initiated and concluded at specific times, provided that the specimen collection study is complete. (OBI:0000471)';
COMMENT ON COLUMN "Specimen measurement study"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';
COMMENT ON COLUMN "Specimen measurement study"."Assay" IS 'The plan design for the assessment of a subject or specimen for a specific feature. Usually the feature is quantitative. Usually the feature is also epistemologically elementary, as contrasted with assessments involving extensive reasoned judgement (as in a full-fledged diagnosis). (OBI:0500000)';
COMMENT ON COLUMN "Specimen measurement study"."Machine" IS 'A machine or tool used by an operator to make measurements of specific properties of subjects or specimens. (OBI:0000832)';
COMMENT ON COLUMN "Specimen measurement study"."Software" IS 'Software that runs on a computer linked to a measurement apparatus to control the measurement process or extract data results. (IAO:0000010)';
COMMENT ON COLUMN "Specimen measurement study"."Inception date" IS 'The initial date of the continuants existence. (NCIT:C68616)';
COMMENT ON COLUMN "Specimen measurement study"."Conclusion date" IS 'The final date of the continuants existence. (NCIT:C68617)';

CREATE TABLE IF NOT EXISTS "Specimen data measurement process" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Specimen" VARCHAR(512) REFERENCES "Specimen collection process"("Specimen") ON DELETE CASCADE ,
    "Specimen age" VARCHAR,
    "Date of measurement" VARCHAR(512),
    "Study" VARCHAR(512) REFERENCES "Specimen measurement study"("Name") ON DELETE CASCADE 
);
COMMENT ON TABLE "Specimen data measurement process" IS 'A process in which a biospecimen is subject to measurement of some qualitative or quantitative feature, usually by means of some measurement apparatus, resulting in a data item or data items about the biospecimen. (OBI:0000070)';
COMMENT ON COLUMN "Specimen data measurement process"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Specimen data measurement process"."Specimen" IS 'The biospecimen analyzed by an analysis process, in case the subject is a biospecimen.';
COMMENT ON COLUMN "Specimen data measurement process"."Specimen age" IS 'The amount of time between the inception of a given biospecimen (typically extraction) and the given event. Typically denominated in number of days. (PATO:0000011)';
COMMENT ON COLUMN "Specimen data measurement process"."Date of measurement" IS 'The time at which something happens. When represented by a string, the preferred format is ISO 8601-1:2019 (e.g. 1999-04-01 for April 1st in the year 1999), but this can also be represented as a timestamp or even a relative, ordinal value, so long as it is consistent across related records.';
COMMENT ON COLUMN "Specimen data measurement process"."Study" IS 'An effort, generally undertaken by a group of collaborating participants, to make data measurements on a collection of biological specimens. Typically initiated and concluded at specific times, provided that the specimen collection study is complete. (OBI:0000471)';

CREATE TABLE IF NOT EXISTS "Data file" (
    "SHA256 hash" VARCHAR(512) PRIMARY KEY,
    "File name" VARCHAR(512),
    "File format" VARCHAR(512),
    "Contents format" VARCHAR(512),
    "Size" VARCHAR(512),
    "Source generation process" VARCHAR(512) REFERENCES "Specimen data measurement process"("Identifier") ON DELETE CASCADE 
);
COMMENT ON TABLE "Data file" IS 'A concrete data artifact (byte string) whose contents represent the empirical-evidential component of a claim or claims about a given material entity. (IAO:0000027)';
COMMENT ON COLUMN "Data file"."SHA256 hash" IS 'The SHA256 hash (Secure Hash Algorithm 2, 256-bit digest) of the contents of a given digital file. (NCIT:C68725)';
COMMENT ON COLUMN "Data file"."File name" IS 'The basename, i.e. without path information, for a file in some file system. A basename implicitly encoding information about the referents of file contents is not preferred; the SHA256 file hash is a reasonable choice of name convention which eschews implicit information (no SHA256 collisions are currently known).';
COMMENT ON COLUMN "Data file"."File format" IS 'A class of file content structures delimited by rough structural criteria. Often indicated with a file extension. For example, comma-separated values (CSV). (NCIT:C171252)';
COMMENT ON COLUMN "Data file"."Contents format" IS 'A documented reference specification for a given class of files which provides a way to parse the semantic meaning of specification-compliant files. (IAO:0000098)';
COMMENT ON COLUMN "Data file"."Size" IS 'The number of bytes in the byte string contents of a given digital file. (NCIT:C171192)';
COMMENT ON COLUMN "Data file"."Source generation process" IS 'The measurement process which produced a given data file.';

CREATE TABLE IF NOT EXISTS "Histological structure" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Anatomical entity" VARCHAR(512)
);
COMMENT ON TABLE "Histological structure" IS 'An instance of an anatomical entity identifiable in tissue sections. For example, a cell, a stromal region, or a subcellular compartment like a nucleus. (UBERON:0000061)';
COMMENT ON COLUMN "Histological structure"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Histological structure"."Anatomical entity" IS 'A part of a structural body pattern consistently observed across a class of organisms. For example cell, nucleus, cytoplasm, membrane, stroma, epithelium, liver. (UBERON:0001062)';

CREATE TABLE IF NOT EXISTS "Shape file" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Geometry specification file format" VARCHAR(512),
    "Base64 contents" VARCHAR
);
COMMENT ON TABLE "Shape file" IS 'A concrete data artifact representing a specific shape in the standard reference dimensionless coordinate space of a given dimension (the standard Euclidean space). For example, a representation of the unit circle in the coordinate plane, a closed polygon with specific enumerated vertices, or a single point. (PATO:0000052)';
COMMENT ON COLUMN "Shape file"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Shape file"."Geometry specification file format" IS 'The documented file format for a given shape specification file.';
COMMENT ON COLUMN "Shape file"."Base64 contents" IS 'The Base64-encoded ASCII character string serialization of the file contents byte string. The encoding is specified by RFC 4648. (NCIT:C47879)';

CREATE TABLE IF NOT EXISTS "Plane coordinates reference system" (
    "Name" VARCHAR(512) PRIMARY KEY,
    "Reference point" VARCHAR,
    "Reference point coordinate 1" NUMERIC,
    "Reference point coordinate 2" NUMERIC,
    "Reference orientation" VARCHAR,
    "Length unit" VARCHAR
);
COMMENT ON TABLE "Plane coordinates reference system" IS 'A correspondence between a specific two-dimensional material or spatial area (or class of such areas under specific conditions) and the standard two-dimensional coordinate space, in the special case of intrinsically-flat areas and correspondences which preserve distances up to an overall scale. Such a correspondence is determined uniquely by (i) a correspondence between just one reference point on the source and target, (ii) an indication of the direction of the first coordinate axis on the referent, (iii) the choice of one of the two possible directions of the remaining, second coordinate axis direction on the referent, and (iv) a choice of length scale, or unit. (STATO:0000010)';
COMMENT ON COLUMN "Plane coordinates reference system"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';
COMMENT ON COLUMN "Plane coordinates reference system"."Reference point" IS 'The description of a single point, on the object or area of focus, which serves as a reference point for establishing an orthogonal (Euclidean similarity) coordinate system. (NCIT:C45793)';
COMMENT ON COLUMN "Plane coordinates reference system"."Reference point coordinate 1" IS 'The intended first coordinate value of the coordinate-space point corresponding to the reference point. For orthogonal (Euclidean similarity) coordinate systems. (IAO:0000402)';
COMMENT ON COLUMN "Plane coordinates reference system"."Reference point coordinate 2" IS 'The intended second coordinate value of the coordinate-space point corresponding to the reference point. For orthogonal (Euclidean similarity) coordinate systems. (IAO:0000402)';
COMMENT ON COLUMN "Plane coordinates reference system"."Reference orientation" IS 'The description of the direction, on the object or area of interest, intended to correspond to the first coordinate positive axis, plus a description of the choice of which of the two orthogonal directions is intended to correspond to the second coordinate positive axis. (PATO:0000133)';
COMMENT ON COLUMN "Plane coordinates reference system"."Length unit" IS 'A representation (e.g. 10 micrometers) of the length unit intended to correspond to the displacement in the coordinate space by the value 1. For orthogonal (Euclidean similarity) coordinate systems. (UO:0000001)';

CREATE TABLE IF NOT EXISTS "Histological structure identification" (
    "Histological structure" VARCHAR(512) REFERENCES "Histological structure"("Identifier") ON DELETE CASCADE ,
    "Data source" VARCHAR(512) REFERENCES "Data file"("SHA256 hash") ON DELETE CASCADE ,
    "Shape file" VARCHAR(512) REFERENCES "Shape file"("Identifier") ON DELETE CASCADE ,
    "Plane coordinates reference" VARCHAR(512) REFERENCES "Plane coordinates reference system"("Name") ON DELETE CASCADE ,
    "Identification method" VARCHAR(512),
    "Identification date" VARCHAR(512),
    "Annotator" VARCHAR
);
COMMENT ON TABLE "Histological structure identification" IS 'A specific instance of identification or delimitation of a histological structure in a slide by means of data measurements, e.g. imaging, resulting in a shape specification defined with respect to a plane coordinates reference system. (NCIT:C80146)';
COMMENT ON COLUMN "Histological structure identification"."Histological structure" IS 'An instance of an anatomical entity identifiable in tissue sections. For example, a cell, a stromal region, or a subcellular compartment like a nucleus. (UBERON:0000061)';
COMMENT ON COLUMN "Histological structure identification"."Data source" IS 'A concrete data artifact (byte string) whose contents represent the empirical-evidential component of a claim or claims about a given material entity. (IAO:0000027)';
COMMENT ON COLUMN "Histological structure identification"."Shape file" IS 'A concrete data artifact representing a specific shape in the standard reference dimensionless coordinate space of a given dimension (the standard Euclidean space). For example, a representation of the unit circle in the coordinate plane, a closed polygon with specific enumerated vertices, or a single point. (PATO:0000052)';
COMMENT ON COLUMN "Histological structure identification"."Plane coordinates reference" IS 'A correspondence between a specific two-dimensional material or spatial area (or class of such areas under specific conditions) and the standard two-dimensional coordinate space, in the special case of intrinsically-flat areas and correspondences which preserve distances up to an overall scale. Such a correspondence is determined uniquely by (i) a correspondence between just one reference point on the source and target, (ii) an indication of the direction of the first coordinate axis on the referent, (iii) the choice of one of the two possible directions of the remaining, second coordinate axis direction on the referent, and (iv) a choice of length scale, or unit. (STATO:0000010)';
COMMENT ON COLUMN "Histological structure identification"."Identification method" IS 'The method by which an annotator identifies or delimits histological structures, instances of an anatomical entity, in a histology slide. For example, manual marking on an image representation of the slide area, or a segmentation algorithm. (OBI:0000272)';
COMMENT ON COLUMN "Histological structure identification"."Identification date" IS 'The time at which something happens. When represented by a string, the preferred format is ISO 8601-1:2019 (e.g. 1999-04-01 for April 1st in the year 1999), but this can also be represented as a timestamp or even a relative, ordinal value, so long as it is consistent across related records.';
COMMENT ON COLUMN "Histological structure identification"."Annotator" IS 'The person who identified a histological structure or operated software making such an identification. (OBI:0001950)';

CREATE TABLE IF NOT EXISTS "Chemical species" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Symbol" VARCHAR,
    "Name" VARCHAR(512),
    "Chemical structure class" VARCHAR(512)
);
COMMENT ON TABLE "Chemical species" IS 'A class of chemical objects, or specific mixture of such objects, defined by structural criteria at the molecular length scale. For example, iron, sodium chloride, keratin, or mRNA molecule coded as the BCL2 gene. (CHEBI:60003)';
COMMENT ON COLUMN "Chemical species"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Chemical species"."Symbol" IS 'A symbol string representation of the chemical species, or possibly a gene class of closely-related species (for example, BCL2 for a certain DNA segment, the corresponding mRNA molecule, and the corresponding protein product).';
COMMENT ON COLUMN "Chemical species"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';
COMMENT ON COLUMN "Chemical species"."Chemical structure class" IS 'A common higher taxon for chemical species, for example mRNA, DNA, protein, lipid, hydrocarbon. Often meant to aid in distinctions between species closely related in an information-theoretic sense, e.g. the distinction between the BCL2 genes mRNA molecule, DNA segment, or protein product. (FMA:63887)';

CREATE TABLE IF NOT EXISTS "Expression quantification" (
    "Histological structure" VARCHAR(512) REFERENCES "Histological structure"("Identifier") ON DELETE CASCADE ,
    "Target" VARCHAR(512) REFERENCES "Chemical species"("Identifier") ON DELETE CASCADE ,
    "Quantity" NUMERIC,
    "Unit" VARCHAR(512),
    "Quantification method" VARCHAR(512),
    "Discrete value" VARCHAR(512),
    "Discretization method" VARCHAR(512)
);
COMMENT ON TABLE "Expression quantification" IS 'An instance of determination of a quantity representing the amount of a chemical target present in a given specimen or structure, typically by means of a specific chemical marking ensemble rendering this amount as an observable quantity (e.g. immunofluoresence at a specific wavelength). (OBI:0003142)';
COMMENT ON COLUMN "Expression quantification"."Histological structure" IS 'The histological structure which is the domain for the given expression quantification process.';
COMMENT ON COLUMN "Expression quantification"."Target" IS 'The chemical species which is quantified by a given process.';
COMMENT ON COLUMN "Expression quantification"."Quantity" IS 'A real (dimensionless) numerical value representing an amount with respect to some unit. (NCIT:C25256)';
COMMENT ON COLUMN "Expression quantification"."Unit" IS 'For a 1-dimensional quantifiable/measurable property forming an abstract additive number system, i.e. exhibiting a natural addition operation, a unit is a choice of reference value for the property. Such a choice determines a correspondence between the possible values of the property and the standard 1-dimensional coordinate space, the (dimensionless) real numbers. (UO:0000000)';
COMMENT ON COLUMN "Expression quantification"."Quantification method" IS 'The method by which marker presence is quantified. For example, averaging of raster image intensity values over an image mask. (STATO:0000039)';
COMMENT ON COLUMN "Expression quantification"."Discrete value" IS 'An information-theoretic entity representing one from among several pre-defined mutually exclusive values for some property. Often derived from a classification of a quantitative value using thresholds. Often one of two pre-defined values, positive and negative. (OBI:0001930)';
COMMENT ON COLUMN "Expression quantification"."Discretization method" IS 'The method by which the quantitative values of some property are cast into discrete values. For example, thresholding on the median over a collection. (STATO:0000213)';

CREATE TABLE IF NOT EXISTS "Biological marking system" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Target" VARCHAR(512) REFERENCES "Chemical species"("Identifier") ON DELETE CASCADE ,
    "Antibody" VARCHAR,
    "Marking mechanism" VARCHAR(512),
    "Study" VARCHAR(512) REFERENCES "Specimen measurement study"("Name") ON DELETE CASCADE 
);
COMMENT ON TABLE "Biological marking system" IS 'An ensemble consisting of an antibody and its target antigen, intended to be used to elicit a specific observable reaction which indicates (marks) antigen presence, often in tissue specimens but also in individual cells or other biospecimens. Developed or selected for use in a given study. (OBI:0003146)';
COMMENT ON COLUMN "Biological marking system"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Biological marking system"."Target" IS 'A class of chemical objects, or specific mixture of such objects, defined by structural criteria at the molecular length scale. For example, iron, sodium chloride, keratin, or mRNA molecule coded as the BCL2 gene. (CHEBI:60003)';
COMMENT ON COLUMN "Biological marking system"."Antibody" IS 'The antibody used in the given marker/staining system.';
COMMENT ON COLUMN "Biological marking system"."Marking mechanism" IS 'The mechanism by which the given marker system renders the target antigen observable. (OBI:0003146)';
COMMENT ON COLUMN "Biological marking system"."Study" IS 'An effort, generally undertaken by a group of collaborating participants, to make data measurements on a collection of biological specimens. Typically initiated and concluded at specific times, provided that the specimen collection study is complete. (OBI:0000471)';

CREATE TABLE IF NOT EXISTS "Data analysis study" (
    "Name" VARCHAR(512) PRIMARY KEY
);
COMMENT ON TABLE "Data analysis study" IS 'An effort, generally undertaken by a group of collaborating participants, to analyze data measurements. (OBI:0200000)';
COMMENT ON COLUMN "Data analysis study"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';

CREATE TABLE IF NOT EXISTS "Cell phenotype" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Symbol" VARCHAR,
    "Name" VARCHAR(512)
);
COMMENT ON TABLE "Cell phenotype" IS 'An in-principle observable character for a cell. Meant to be inclusive of potentially-transient cell states and more enduring cell types. (CL:0000000PHENOTYPE)';
COMMENT ON COLUMN "Cell phenotype"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Cell phenotype"."Symbol" IS 'A symbol string, not necessarily intended for verbalization in long-form speech or text, meant to summarize the intended meaning of a given cell phenotype. This is potentially an abbreviation of the full name.';
COMMENT ON COLUMN "Cell phenotype"."Name" IS 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text. (IAO:0000590)';

CREATE TABLE IF NOT EXISTS "Cell phenotype criterion" (
    "Cell phenotype" VARCHAR(512) REFERENCES "Cell phenotype"("Identifier") ON DELETE CASCADE ,
    "Marker" VARCHAR(512) REFERENCES "Chemical species"("Identifier") ON DELETE CASCADE ,
    "Polarity" VARCHAR(512),
    "Study" VARCHAR(512) REFERENCES "Data analysis study"("Name") ON DELETE CASCADE 
);
COMMENT ON TABLE "Cell phenotype criterion" IS 'A criterion which must be satisfied by a cell in order that it acquire the designation of a specific phenotype. Typically a suitable amount of membrane expression of a certain protein or other chemical species. The latter is often a Cluster of Differentiation (CD) protein, especially for immune cell phenotypes. The criteria used (and the phenotypes themselves) may depend on the specific data analysis study undertaken.';
COMMENT ON COLUMN "Cell phenotype criterion"."Cell phenotype" IS 'An in-principle observable character for a cell. Meant to be inclusive of potentially-transient cell states and more enduring cell types. (CL:0000000PHENOTYPE)';
COMMENT ON COLUMN "Cell phenotype criterion"."Marker" IS 'The chemical species whose presence or absence is the substance of a given cell phenotype criterion.';
COMMENT ON COLUMN "Cell phenotype criterion"."Polarity" IS 'The value (typically positive or negative) stipulated by a given cell phenotype criterion.';
COMMENT ON COLUMN "Cell phenotype criterion"."Study" IS 'An effort, generally undertaken by a group of collaborating participants, to analyze data measurements. (OBI:0200000)';

CREATE TABLE IF NOT EXISTS "Feature specification" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Derivation method" VARCHAR(512),
    "Study" VARCHAR(512) REFERENCES "Data analysis study"("Name") ON DELETE CASCADE 
);
COMMENT ON TABLE "Feature specification" IS 'An information content entity using enumerated specifiers to describe one from among several possible feature derivations. (OBI:0001892)';
COMMENT ON COLUMN "Feature specification"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Feature specification"."Derivation method" IS 'The plan for a computational or experimental process that results in associations of quantitative (or, sometimes, qualitative) values to elements of a sample set. Often the associations involve an aggregation over finer-grained samples to a coarsest level of granularity, and are dependent on enumerated specifiers, like an ordered tuple of genes or image channels. (OBI:0001028)';
COMMENT ON COLUMN "Feature specification"."Study" IS 'An effort, generally undertaken by a group of collaborating participants, to analyze data measurements. (OBI:0200000)';

CREATE TABLE IF NOT EXISTS "Feature specifier" (
    "Feature specification" VARCHAR(512) REFERENCES "Feature specification"("Identifier") ON DELETE CASCADE ,
    "Specifier" VARCHAR(512),
    "Ordinality" VARCHAR(512)
);
COMMENT ON TABLE "Feature specifier" IS 'A specifier that is an enumerated part of some feature specification.';
COMMENT ON COLUMN "Feature specifier"."Feature specification" IS 'An information content entity using enumerated specifiers to describe one from among several possible feature derivations. (OBI:0001892)';
COMMENT ON COLUMN "Feature specifier"."Specifier" IS 'An identifier meant to be used in a limited context, for disambiguation between highly salient alternatives.';
COMMENT ON COLUMN "Feature specifier"."Ordinality" IS 'A data value that is an ordinal number, ie., a number that tells the position of something in a list. (OBCS:0000196)';

CREATE TABLE IF NOT EXISTS "Quantitative feature value" (
    "Identifier" VARCHAR(512) PRIMARY KEY,
    "Feature" VARCHAR(512) REFERENCES "Feature specification"("Identifier") ON DELETE CASCADE ,
    "Subject" VARCHAR(512),
    "Value" NUMERIC
);
COMMENT ON TABLE "Quantitative feature value" IS 'An instance of quantification of a state or property of a subject which is carried out according to a given feature specification.';
COMMENT ON COLUMN "Quantitative feature value"."Identifier" IS 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text. (OPMI:0000413)';
COMMENT ON COLUMN "Quantitative feature value"."Feature" IS 'The specification for feature derivation which was used to carry out a given instance of quantification.';
COMMENT ON COLUMN "Quantitative feature value"."Subject" IS 'The entity that was subjected to the feature derivation or quantification process.';
COMMENT ON COLUMN "Quantitative feature value"."Value" IS 'The quantity resulting from the quantification process.';

CREATE TABLE IF NOT EXISTS "Two-cohort feature association test" (
    "Selection criterion 1" VARCHAR(512) REFERENCES "Diagnostic selection criterion"("Identifier") ON DELETE CASCADE ,
    "Selection criterion 2" VARCHAR(512) REFERENCES "Diagnostic selection criterion"("Identifier") ON DELETE CASCADE ,
    "Test" VARCHAR(512),
    "p-value" NUMERIC,
    "Feature tested" VARCHAR(512) REFERENCES "Feature specification"("Identifier") ON DELETE CASCADE 
);
COMMENT ON TABLE "Two-cohort feature association test" IS 'An application of a statistical test for association between a given specified feature on a sample set and assignment to one of two cohorts defined by selection criteria. (STATO:0000279)';
COMMENT ON COLUMN "Two-cohort feature association test"."Selection criterion 1" IS 'A criterion for cohort selection on the basis of a diagnosis result. (OBI:0001755)';
COMMENT ON COLUMN "Two-cohort feature association test"."Selection criterion 2" IS 'A criterion for cohort selection on the basis of a diagnosis result. (OBI:0001755)';
COMMENT ON COLUMN "Two-cohort feature association test"."Test" IS 'See OBI. (OBI:0000673)';
COMMENT ON COLUMN "Two-cohort feature association test"."p-value" IS 'See OBI. (OBI:0000175)';
COMMENT ON COLUMN "Two-cohort feature association test"."Feature tested" IS 'An information content entity using enumerated specifiers to describe one from among several possible feature derivations. (OBI:0001892)';

CREATE TABLE IF NOT EXISTS "Permanent condition diagnosis" (
    "Condition" VARCHAR(512),
    "Result" VARCHAR(512)
);
COMMENT ON TABLE "Permanent condition diagnosis" IS 'A class of diagnoses for a specific condition for which a specific result indicates that a certain permanent effect has manifested in the subject. This can be either an inherently permanent effect (like death), or a synthetically permanent effect (like the subject has experienced a recurrence event at some point in the past, regarded as a state of the subject).';
COMMENT ON COLUMN "Permanent condition diagnosis"."Condition" IS 'An an-principle empirically diagnosable condition of a subject. (BFO:0000016)';
COMMENT ON COLUMN "Permanent condition diagnosis"."Result" IS 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer). (OGMS:0000073)';

CREATE TABLE IF NOT EXISTS "Condition lack" (
    "Condition" VARCHAR(512),
    "Presence result" VARCHAR(512),
    "Absence result" VARCHAR(512)
);
COMMENT ON TABLE "Condition lack" IS 'The relation holding between two specific condition observations where the latter is precisely the observation of the lack of the former up to observation time.';
COMMENT ON COLUMN "Condition lack"."Condition" IS 'An an-principle empirically diagnosable condition of a subject. (BFO:0000016)';
COMMENT ON COLUMN "Condition lack"."Presence result" IS 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer). (OGMS:0000073)';
COMMENT ON COLUMN "Condition lack"."Absence result" IS 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer). (OGMS:0000073)';

CREATE TABLE "reference_tables" (
"Name" TEXT,
  "Label" TEXT,
  "Filename" TEXT,
  "Entity" TEXT
);
INSERT INTO reference_tables VALUES ('study', 'Study', 'study.tsv', 'Investigation'),
       ('research_professional', 'Research professional', 'research_professional.tsv', 'Research professional'),
       ('study_contact_person', 'Study contact person', 'study_contact_person.tsv', 'Study contact person'),
       ('study_component', 'Study component', 'study_component.tsv', 'Study component'),
       ('publication', 'Publication', 'publication.tsv', 'Publication'),
       ('author', 'Author', 'author.tsv', 'Author'),
       ('subject', 'Subject', 'subject.tsv', 'Study subject'),
       ('diagnosis', 'Diagnosis', 'diagnosis.tsv', 'Diagnosis event'),
       ('diagnostic_selection_criterion', 'Diagnostic selection criterion', 'diagnostic_selection_criterion.tsv', 'Diagnostic selection criterion'),
       ('intervention', 'Intervention', 'intervention.tsv', 'Intervention'),
       ('specimen_collection_study', 'Specimen collection study', 'specimen_collection_study.tsv', 'Biospecimen collection study'),
       ('specimen_collection_process', 'Specimen collection process', 'specimen_collection_process.tsv', 'Biospecimen collection process'),
       ('histology_assessment_process', 'Histology assessment process', 'histology_assessment_process.tsv', 'Histology assessment process'),
       ('specimen_measurement_study', 'Specimen measurement study', 'specimen_measurement_study.tsv', 'Biospecimen data measurement study'),
       ('specimen_data_measurement_process', 'Specimen data measurement process', 'specimen_data_measurement_process.tsv', 'Biospecimen data measurement process'),
       ('data_file', 'Data file', 'data_file.tsv', 'Data file'),
       ('histological_structure', 'Histological structure', 'histological_structure.tsv', 'Histological structure'),
       ('shape_file', 'Shape file', 'shape_file.tsv', 'Coordinate shape specification'),
       ('plane_coordinates_reference_system', 'Plane coordinates reference system', 'plane_coordinates_reference_system.tsv', 'Plane coordinates reference system'),
       ('histological_structure_identification', 'Histological structure identification', 'histological_structure_identification.tsv', 'Histological structure identification process'),
       ('chemical_species', 'Chemical species', 'chemical_species.tsv', 'Chemical species'),
       ('expression_quantification', 'Expression quantification', 'expression_quantification.tsv', 'Quantification of chemical target expression'),
       ('biological_marking_system', 'Biological marking system', 'biological_marking_system.tsv', 'Biological marking system'),
       ('data_analysis_study', 'Data analysis study', 'data_analysis_study.tsv', 'Data analysis study'),
       ('cell_phenotype', 'Cell phenotype', 'cell_phenotype.tsv', 'Cell phenotype'),
       ('cell_phenotype_criterion', 'Cell phenotype criterion', 'cell_phenotype_criterion.tsv', 'Cell phenotype criterion'),
       ('feature_specification', 'Feature specification', 'feature_specification.tsv', 'Feature specification'),
       ('feature_specifier', 'Feature specifier', 'feature_specifier.tsv', 'Feature specifier'),
       ('quantitative_feature_value', 'Quantitative feature value', 'quantitative_feature_value.tsv', 'Quantitative feature derivation process'),
       ('two_cohort_feature_association_test', 'Two-cohort feature association test', 'two_cohort_feature_association_test.tsv', 'Two-cohort feature association test'),
       ('permanent_condition_diagnosis', 'Permanent condition diagnosis', 'permanent_condition_diagnosis.tsv', 'Permanent condition diagnosis'),
       ('condition_lack', 'Condition lack', 'condition_lack.tsv', 'Condition lack');

CREATE TABLE "reference_fields" (
"Name" TEXT,
  "Label" TEXT,
  "Table" TEXT,
  "Property" TEXT,
  "Primary key group" TEXT,
  "Foreign table" TEXT,
  "Foreign key" TEXT,
  "Ordinality" INTEGER
);
INSERT INTO reference_fields VALUES ('identifier', 'Identifier', 'Subject', 'Identifier', '1', '', '', 1),
       ('species', 'Species', 'Subject', 'Biological species', '', '', '', 2),
       ('sex', 'Sex', 'Subject', 'Phenotypic sex', '', '', '', 3),
       ('birth_date', 'Birth date', 'Subject', 'Date of birth', '', '', '', 4),
       ('death_date', 'Death date', 'Subject', 'Date of death', '', '', '', 5),
       ('cause_of_death', 'Cause of death', 'Subject', 'Cause of death', '', '', '', 6),
       ('subject', 'Subject', 'Diagnosis', 'Study subject', '', 'Subject', 'Identifier', 1),
       ('condition', 'Condition', 'Diagnosis', 'Condition considered', '', '', '', 2),
       ('result', 'Result', 'Diagnosis', 'Diagnosis result', '', '', '', 3),
       ('assessor', 'Assessor', 'Diagnosis', 'Diagnosis assessor', '', '', '', 4),
       ('date', 'Date', 'Diagnosis', 'Date of diagnosis', '', '', '', 5),
       ('date_of_evidence', 'Date of evidence', 'Diagnosis', 'Maximal date of evidence', '', '', '', 6),
       ('identifier', 'Identifier', 'Diagnostic selection criterion', 'Identifier', '1', '', '', 1),
       ('condition', 'Condition', 'Diagnostic selection criterion', 'Condition', '', '', '', 2),
       ('result', 'Result', 'Diagnostic selection criterion', 'Diagnosis result', '', '', '', 3),
       ('specimen', 'Specimen', 'Specimen collection process', 'Extracted subspecimen', '1', '', '', 1),
       ('source', 'Source', 'Specimen collection process', 'Source biospecimen', '', '', '', 2),
       ('source_site', 'Source site', 'Specimen collection process', 'Subspecimen extraction site', '', '', '', 3),
       ('source_age', 'Source age', 'Specimen collection process', 'Biospecimen age at event', '', '', '', 4),
       ('extraction_date', 'Extraction date', 'Specimen collection process', 'Event date', '', '', '', 5),
       ('study', 'Study', 'Specimen collection process', 'Biospecimen collection study', '', 'Specimen collection study', 'Name', 6),
       ('name', 'Name', 'Specimen collection study', 'Name', '1', '', '', 1),
       ('extraction_method', 'Extraction method', 'Specimen collection study', 'Subspecimen extraction method', '', '', '', 2),
       ('preservation_method', 'Preservation method', 'Specimen collection study', 'Biospecimen preservation method', '', '', '', 3),
       ('storage_location', 'Storage location', 'Specimen collection study', 'Biospecimen storage location', '', '', '', 4),
       ('inception_date', 'Inception date', 'Specimen collection study', 'Date of inception', '', '', '', 5),
       ('conclusion_date', 'Conclusion date', 'Specimen collection study', 'Date of conclusion', '', '', '', 6),
       ('slide', 'Slide', 'Histology assessment process', 'Histology slide', '', 'Specimen collection process', 'Specimen', 1),
       ('assay', 'Assay', 'Histology assessment process', 'Histology assay', '', '', '', 2),
       ('result', 'Result', 'Histology assessment process', 'Assay result', '', '', '', 3),
       ('assessor', 'Assessor', 'Histology assessment process', 'Assay performer', '', '', '', 4),
       ('assessment_date', 'Assessment date', 'Histology assessment process', 'Event date', '', '', '', 5),
       ('identifier', 'Identifier', 'Specimen data measurement process', 'Identifier', '1', '', '', 1),
       ('specimen', 'Specimen', 'Specimen data measurement process', 'Biospecimen analyzed', '', 'Specimen collection process', 'Specimen', 2),
       ('specimen_age', 'Specimen age', 'Specimen data measurement process', 'Biospecimen age at event', '', '', '', 3),
       ('date_of_measurement', 'Date of measurement', 'Specimen data measurement process', 'Event date', '', '', '', 4),
       ('study', 'Study', 'Specimen data measurement process', 'Biospecimen data measurement study', '', 'Specimen measurement study', 'Name', 5),
       ('name', 'Name', 'Specimen measurement study', 'Name', '1', '', '', 1),
       ('assay', 'Assay', 'Specimen measurement study', 'Measurement assay', '', '', '', 2),
       ('machine', 'Machine', 'Specimen measurement study', 'Measurement apparatus', '', '', '', 3),
       ('software', 'Software', 'Specimen measurement study', 'Measurement apparatus software', ' ', '', '', 4),
       ('inception_date', 'Inception date', 'Specimen measurement study', 'Date of inception', '', '', '', 5),
       ('conclusion_date', 'Conclusion date', 'Specimen measurement study', 'Date of conclusion', '', '', '', 6),
       ('sha256_hash', 'SHA256 hash', 'Data file', 'File hash SHA256', '1', '', '', 1),
       ('file_name', 'File name', 'Data file', 'File basename', '', '', '', 2),
       ('file_format', 'File format', 'Data file', 'File syntax format', '', '', '', 3),
       ('contents_format', 'Contents format', 'Data file', 'File content structure specification', '', '', '', 4),
       ('size', 'Size', 'Data file', 'File size', '', '', '', 5),
       ('source_generation_process', 'Source generation process', 'Data file', 'Data file generation source process', '', 'Specimen data measurement process', 'Identifier', 6),
       ('identifier', 'Identifier', 'Histological structure', 'Identifier', '1', '', '', 1),
       ('anatomical_entity', 'Anatomical entity', 'Histological structure', 'Anatomical entity', '', '', '', 2),
       ('histological_structure', 'Histological structure', 'Histological structure identification', 'Histological structure', '1', 'Histological structure', 'Identifier', 1),
       ('data_source', 'Data source', 'Histological structure identification', 'Data file', '', 'Data file', 'SHA256 hash', 2),
       ('shape_file', 'Shape file', 'Histological structure identification', 'Coordinate shape specification', '', 'Shape file', 'Identifier', 3),
       ('plane_coordinates_reference', 'Plane coordinates reference', 'Histological structure identification', 'Plane coordinates reference system', '', 'Plane coordinates reference system', 'Name', 4),
       ('identification_method', 'Identification method', 'Histological structure identification', 'Histological structure identification method', '', '', '', 5),
       ('identification_date', 'Identification date', 'Histological structure identification', 'Event date', '', '', '', 6),
       ('annotator', 'Annotator', 'Histological structure identification', 'Histological structure identification performer', '', '', '', 7),
       ('identifier', 'Identifier', 'Shape file', 'Identifier', '1', '', '', 1),
       ('geometry_specification_file_format', 'Geometry specification file format', 'Shape file', 'Shape specification file format', '', '', '', 2),
       ('base64_contents', 'Base64 contents', 'Shape file', 'Base64 file contents', '', '', '', 3),
       ('name', 'Name', 'Plane coordinates reference system', 'Name', '1', '', '', 1),
       ('reference_point', 'Reference point', 'Plane coordinates reference system', 'Coordinate system reference point', '', '', '', 2),
       ('reference_point_coordinate_1', 'Reference point coordinate 1', 'Plane coordinates reference system', 'Coordinate system reference point 1', '', '', '', 3),
       ('reference_point_coordinate_2', 'Reference point coordinate 2', 'Plane coordinates reference system', 'Coordinate system reference point 2', '', '', '', 4),
       ('reference_orientation', 'Reference orientation', 'Plane coordinates reference system', 'Coordinate system orientation specification', '', '', '', 5),
       ('length_unit', 'Length unit', 'Plane coordinates reference system', 'Coordinate system unit', '', '', '', 6),
       ('histological_structure', 'Histological structure', 'Expression quantification', 'Subject of quantification', '', 'Histological structure', 'Identifier', 1),
       ('target', 'Target', 'Expression quantification', 'Chemical species quantified', '', 'Chemical species', 'Identifier', 2),
       ('quantity', 'Quantity', 'Expression quantification', 'Expression quantity', '', '', '', 3),
       ('unit', 'Unit', 'Expression quantification', 'Unit', '', '', '', 4),
       ('quantification_method', 'Quantification method', 'Expression quantification', 'Method of marker quantification', '', '', '', 5),
       ('discrete_value', 'Discrete value', 'Expression quantification', 'Discrete value', '', '', '', 6),
       ('discretization_method', 'Discretization method', 'Expression quantification', 'Method of marker discretization', '', '', '', 7),
       ('identifier', 'Identifier', 'Biological marking system', 'Identifier', '1', '', '', 1),
       ('target', 'Target', 'Biological marking system', 'Chemical species', '', 'Chemical species', 'Identifier', 2),
       ('antibody', 'Antibody', 'Biological marking system', 'Marking antibody', '', '', '', 3),
       ('marking_mechanism', 'Marking mechanism', 'Biological marking system', 'Mechanism of target marking', '', '', '', 4),
       ('study', 'Study', 'Biological marking system', 'Biospecimen data measurement study', '', 'Specimen measurement study', 'Name', 5),
       ('identifier', 'Identifier', 'Chemical species', 'Identifier', '1', '', '', 1),
       ('symbol', 'Symbol', 'Chemical species', 'Chemical species symbol', '', '', '', 2),
       ('name', 'Name', 'Chemical species', 'Name', '', '', '', 3),
       ('chemical_structure_class', 'Chemical structure class', 'Chemical species', 'Chemical species structure class', '', '', '', 4),
       ('identifier', 'Identifier', 'Cell phenotype', 'Identifier', '1', '', '', 1),
       ('symbol', 'Symbol', 'Cell phenotype', 'Cell phenotype symbol', '', '', '', 2),
       ('name', 'Name', 'Cell phenotype', 'Name', '', '', '', 3),
       ('cell_phenotype', 'Cell phenotype', 'Cell phenotype criterion', 'Cell phenotype', '', 'Cell phenotype', 'Identifier', 1),
       ('marker', 'Marker', 'Cell phenotype criterion', 'Cell phenotype criterion marker', '', 'Chemical species', 'Identifier', 2),
       ('polarity', 'Polarity', 'Cell phenotype criterion', 'Cell phenotype criterion polarity', '', '', '', 3),
       ('study', 'Study', 'Cell phenotype criterion', 'Data analysis study', '', 'Data analysis study', 'Name', 4),
       ('name', 'Name', 'Data analysis study', 'Name', '1', '', '', 1),
       ('identifier', 'Identifier', 'Feature specification', 'Identifier', '1', '', '', 1),
       ('derivation_method', 'Derivation method', 'Feature specification', 'Feature derivation method', '', '', '', 2),
       ('study', 'Study', 'Feature specification', 'Data analysis study', '', 'Data analysis study', 'Name', 3),
       ('feature_specification', 'Feature specification', 'Feature specifier', 'Feature specification', '1', 'Feature specification', 'Identifier', 1),
       ('specifier', 'Specifier', 'Feature specifier', 'Specifier', '', '', '', 2),
       ('ordinality', 'Ordinality', 'Feature specifier', 'Ordinality', '', '', '', 3),
       ('identifier', 'Identifier', 'Quantitative feature value', 'Identifier', '1', '', '', 1),
       ('feature', 'Feature', 'Quantitative feature value', 'Specification of quantified feature', '', 'Feature specification', 'Identifier', 2),
       ('subject', 'Subject', 'Quantitative feature value', 'Feature subject', '', '', '', 3),
       ('value', 'Value', 'Quantitative feature value', 'Feature value', '', '', '', 4),
       ('selection_criterion_1', 'Selection criterion 1', 'Two-cohort feature association test', 'Diagnostic selection criterion', '', 'Diagnostic selection criterion', 'Identifier', 1),
       ('selection_criterion_2', 'Selection criterion 2', 'Two-cohort feature association test', 'Diagnostic selection criterion', '', 'Diagnostic selection criterion', 'Identifier', 2),
       ('test', 'Test', 'Two-cohort feature association test', 'Statistical test', '', '', '', 3),
       ('p_value', 'p-value', 'Two-cohort feature association test', 'Test probability value', '', '', '', 4),
       ('feature_tested', 'Feature tested', 'Two-cohort feature association test', 'Feature specification', '', 'Feature specification', 'Identifier', 5),
       ('subject', 'Subject', 'Intervention', 'Study subject', '', 'Subject', 'Identifier', 1),
       ('specifier', 'Specifier', 'Intervention', 'Specifier', '', '', '', 2),
       ('date', 'Date', 'Intervention', 'Date of intervention', '', '', '', 3),
       ('study_specifier', 'Study specifier', 'Study', 'Study specifier', '1', '', '', 1),
       ('institution', 'Institution', 'Study', 'Institution of activity', '', '', '', 2),
       ('name', 'Name', 'Study contact person', 'Research professional', '', 'Research professional', 'Full name', 1),
       ('study', 'Study', 'Study contact person', 'Investigation', '', 'Study', 'Study specifier', 2),
       ('contact_reference', 'Contact reference', 'Study contact person', 'Communication contact reference', '', '', '', 3),
       ('primary_study', 'Primary study', 'Study component', 'Primary study', '', '', '', 1),
       ('component_study', 'Component study', 'Study component', 'Component study', '', '', '', 2),
       ('title', 'Title', 'Publication', 'Name', '1', '', '', 1),
       ('study', 'Study', 'Publication', 'Investigation', '', 'Study', 'Study specifier', 2),
       ('document_type', 'Document type', 'Publication', 'Document structure class', '', '', '', 3),
       ('publisher', 'Publisher', 'Publication', 'Publisher', '', '', '', 4),
       ('date_of_publication', 'Date of publication', 'Publication', 'Date of publication', '', '', '', 5),
       ('internet_reference', 'Internet reference', 'Publication', 'Internet reference', '', '', '', 6),
       ('person', 'Person', 'Author', 'Research professional', '', 'Research professional', 'Full name', 1),
       ('publication', 'Publication', 'Author', 'Publication', '', 'Publication', 'Title', 2),
       ('ordinality', 'Ordinality', 'Author', 'Author rank', '', '', '', 3),
       ('full_name', 'Full name', 'Research professional', 'Personal full name', '1', '', '', 1),
       ('surname', 'Surname', 'Research professional', 'Family name', '', '', '', 2),
       ('given_name', 'Given name', 'Research professional', 'Given name', '', '', '', 3),
       ('orcid', 'ORCID', 'Research professional', 'Open researcher and contributor identifier', '', '', '', 4),
       ('condition', 'Condition', 'Permanent condition diagnosis', 'Condition', '', '', '', 1),
       ('result', 'Result', 'Permanent condition diagnosis', 'Diagnosis result', '', '', '', 2),
       ('condition', 'Condition', 'Condition lack', 'Condition', '', '', '', 1),
       ('presence_result', 'Presence result', 'Condition lack', 'Diagnosis result', '', '', '', 2),
       ('absence_result', 'Absence result', 'Condition lack', 'Diagnosis result', '', '', '', 3);

CREATE TABLE "reference_entities" (
"Name" TEXT,
  "Label" TEXT,
  "Definitional reference" TEXT,
  "Definition" TEXT
);
INSERT INTO reference_entities VALUES ('analysis_process', 'Analysis process', 'NCIT:C25391', 'Any act of analysis, broadly construed, of a subject. To include identification, observation, etc.'),
       ('anatomical_entity', 'Anatomical entity', 'UBERON:0001062', 'A part of a structural body pattern consistently observed across a class of organisms. For example cell, nucleus, cytoplasm, membrane, stroma, epithelium, liver.'),
       ('antibody', 'Antibody', '', 'A molecule or other chemical species exhibiting reactivity with a specific target antigen. Especially when the antigen presence is temporally prior or naturally occurring, and the antibody presence is naturally-induced (as in an immune response) or is deliberately introduced (as in histological staining).'),
       ('assay_result', 'Assay result', 'OBI:0001909', 'The empirical claim about a subject supported by an assay analyzing that subject. When the assay type is binary (present or not present), the assay result is just assertion or non-assertion of the claim corresponding to the assay type (for example, an assay for the presence of a specific disease). In this case a common convention for the values is positive or negative.'),
       ('assay', 'Assay', 'OBI:0000070', 'A planned process with the objective to produce information about the material entity that is the evaluant, by physically examining it or its proxies.'),
       ('biological_marking_system', 'Biological marking system', 'OBI:0003146', 'An ensemble consisting of an antibody and its target antigen, intended to be used to elicit a specific observable reaction which indicates (marks) antigen presence, often in tissue specimens but also in individual cells or other biospecimens. Developed or selected for use in a given study.'),
       ('biological_species', 'Biological species', '', 'A collection of organisms whose members are related by a sequence of tokogenies (ancestry/descent), and for which the collection is maximal subject to the constraint it that does not span any speciation boundaries, i.e. temporal boundaries formed by allopatric, parapatric, or sympatric speciation events (Wheeler and Meier, Species Concepts and Phylogenetic Theory). For example, Homo sapiens (humans), or Mus musculus (mice).'),
       ('biospecimen', 'Biospecimen', 'OBI:0100051', 'A portion (or, more rarely, the whole) of an organism prepared to be an object of study, observation, measurement, or analysis.'),
       ('biospecimen_collection_process', 'Biospecimen collection process', 'OBI:0000659', 'A process in which a biospecimen is retrieved from its natural environment or host and placed under control for observation and analysis. Typically the process consists of extraction of a subspecimen from a whole organism, or from another subspecimen, at a specific site, preservation using a specific protocol, and storage together with similar specimens collected as part of a study.'),
       ('biospecimen_collection_study', 'Biospecimen collection study', 'OBI:0000471', 'An effort, generally undertaken by a group of collaborating participants, to collect biospecimens of a particular type for the purpose of eventual observation/measurement and analysis. Typically initiated and concluded at specific times, but may be ongoing.'),
       ('biospecimen_data_measurement_process', 'Biospecimen data measurement process', 'OBI:0000070', 'A process in which a biospecimen is subject to measurement of some qualitative or quantitative feature, usually by means of some measurement apparatus, resulting in a data item or data items about the biospecimen.'),
       ('biospecimen_data_measurement_study', 'Biospecimen data measurement study', 'OBI:0000471', 'An effort, generally undertaken by a group of collaborating participants, to make data measurements on a collection of biological specimens. Typically initiated and concluded at specific times, provided that the specimen collection study is complete.'),
       ('biospecimen_event', 'Biospecimen event', '', 'An event pertaining to a biospecimen. A time in the duration span of the biospecimen.'),
       ('biospecimen_preservation_method', 'Biospecimen preservation method', 'NCIT:C64262', 'A method of treatment of a biospecimen intended to preserve the structure and chemical composition which were present at the time immediately prior to extraction.'),
       ('continuant', 'Continuant', 'BFO:0000002', 'See BFO.'),
       ('cell_phenotype', 'Cell phenotype', 'CL:0000000PHENOTYPE', 'An in-principle observable character for a cell. Meant to be inclusive of potentially-transient cell states and more enduring cell types.'),
       ('cell_phenotype_criterion', 'Cell phenotype criterion', '', 'A criterion which must be satisfied by a cell in order that it acquire the designation of a specific phenotype. Typically a suitable amount of membrane expression of a certain protein or other chemical species. The latter is often a Cluster of Differentiation (CD) protein, especially for immune cell phenotypes. The criteria used (and the phenotypes themselves) may depend on the specific data analysis study undertaken.'),
       ('chemical_species', 'Chemical species', 'CHEBI:60003', 'A class of chemical objects, or specific mixture of such objects, defined by structural criteria at the molecular length scale. For example, iron, sodium chloride, keratin, or mRNA molecule coded as the BCL2 gene.'),
       ('chemical_species_structure_class', 'Chemical species structure class', 'FMA:63887', 'A common higher taxon for chemical species, for example mRNA, DNA, protein, lipid, hydrocarbon. Often meant to aid in distinctions between species closely related in an information-theoretic sense, e.g. the distinction between the BCL2 genes mRNA molecule, DNA segment, or protein product.'),
       ('condition', 'Condition', 'BFO:0000016', 'An an-principle empirically diagnosable condition of a subject.'),
       ('coordinate_shape_specification', 'Coordinate shape specification', 'PATO:0000052', 'A concrete data artifact representing a specific shape in the standard reference dimensionless coordinate space of a given dimension (the standard Euclidean space). For example, a representation of the unit circle in the coordinate plane, a closed polygon with specific enumerated vertices, or a single point.'),
       ('data_analysis_study', 'Data analysis study', 'OBI:0200000', 'An effort, generally undertaken by a group of collaborating participants, to analyze data measurements.'),
       ('data_file', 'Data file', 'IAO:0000027', 'A concrete data artifact (byte string) whose contents represent the empirical-evidential component of a claim or claims about a given material entity.'),
       ('diagnosis_assessor', 'Diagnosis assessor', 'NCIT:C48206', 'The person or agent who performs a given diagnosis.'),
       ('diagnosis_result', 'Diagnosis result', 'OGMS:0000073', 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer).'),
       ('diagnostic_selection_criterion', 'Diagnostic selection criterion', 'OBI:0001755', 'A criterion for cohort selection on the basis of a diagnosis result.'),
       ('discrete_value', 'Discrete value', 'OBI:0001930', 'An information-theoretic entity representing one from among several pre-defined mutually exclusive values for some property. Often derived from a classification of a quantitative value using thresholds. Often one of two pre-defined values, positive and negative.'),
       ('diagnosis_event', 'Diagnosis event', 'OGMS:0000073', 'The concluding event of an assessors determination of the presence or absence of a specific condition in a subject. Often the determination is made on the basis of consideration of multiple factors.'),
       ('event_date', 'Event date', '', 'The time at which something happens. When represented by a string, the preferred format is ISO 8601-1:2019 (e.g. 1999-04-01 for April 1st in the year 1999), but this can also be represented as a timestamp or even a relative, ordinal value, so long as it is consistent across related records.'),
       ('evaluation', 'Evaluation', 'NCIT:C25214', 'Systematic, objective appraisal of the significance, effectiveness, and impact of activities or condition according to specified objectives and criteria.'),
       ('feature_specification', 'Feature specification', 'OBI:0001892', 'An information content entity using enumerated specifiers to describe one from among several possible feature derivations.'),
       ('feature_specifier', 'Feature specifier', '', 'A specifier that is an enumerated part of some feature specification.'),
       ('feature_derivation_method', 'Feature derivation method', 'OBI:0001028', 'The plan for a computational or experimental process that results in associations of quantitative (or, sometimes, qualitative) values to elements of a sample set. Often the associations involve an aggregation over finer-grained samples to a coarsest level of granularity, and are dependent on enumerated specifiers, like an ordered tuple of genes or image channels.'),
       ('file', 'File', '', 'A concrete data artifact consisting of a particular byte string.'),
       ('file_basename', 'File basename', '', 'The basename, i.e. without path information, for a file in some file system. A basename implicitly encoding information about the referents of file contents is not preferred; the SHA256 file hash is a reasonable choice of name convention which eschews implicit information (no SHA256 collisions are currently known).'),
       ('file_content_structure_specification', 'File content structure specification', 'IAO:0000098', 'A documented reference specification for a given class of files which provides a way to parse the semantic meaning of specification-compliant files.'),
       ('file_hash_sha256', 'File hash SHA256', 'NCIT:C68725', 'The SHA256 hash (Secure Hash Algorithm 2, 256-bit digest) of the contents of a given digital file.'),
       ('file_size', 'File size', 'NCIT:C171192', 'The number of bytes in the byte string contents of a given digital file.'),
       ('file_syntax_format', 'File syntax format', 'NCIT:C171252', 'A class of file content structures delimited by rough structural criteria. Often indicated with a file extension. For example, comma-separated values (CSV).'),
       ('histological_structure', 'Histological structure', 'UBERON:0000061', 'An instance of an anatomical entity identifiable in tissue sections. For example, a cell, a stromal region, or a subcellular compartment like a nucleus.'),
       ('histological_structure_identification_method', 'Histological structure identification method', 'OBI:0000272', 'The method by which an annotator identifies or delimits histological structures, instances of an anatomical entity, in a histology slide. For example, manual marking on an image representation of the slide area, or a segmentation algorithm.'),
       ('histological_structure_identification_process', 'Histological structure identification process', 'NCIT:C80146', 'A specific instance of identification or delimitation of a histological structure in a slide by means of data measurements, e.g. imaging, resulting in a shape specification defined with respect to a plane coordinates reference system.'),
       ('histology_assay', 'Histology assay', 'OBI:0001896', 'The assessment (e.g. of a histology slide) for a specific feature. For example, tumor grading.'),
       ('histology_assessment_process', 'Histology assessment process', 'OBI:0600020', 'A specific instance of performance of an histology assay by an assessor at a specific time.'),
       ('histology_slide', 'Histology slide', 'OBI:0400170', 'A biological specimen together with a supporting substrate on which it is mounted. Typically for the purpose of microscopy analysis.'),
       ('identifier', 'Identifier', 'OPMI:0000413', 'A symbol string meant to correspond to exactly one member of a collection. Generally not a linguistic name for verbalization in natural language speech or text.'),
       ('institution', 'Institution', 'NCIT:C41206', 'An established society, corporation, foundation or other organization founded and united for a specific purpose, e.g. for health-related research.'),
       ('intervention', 'Intervention', 'NCIT:C25218', 'An activity that produces an effect, or that is intended to alter the course of a disease in a patient.'),
       ('measurement_apparatus', 'Measurement apparatus', 'OBI:0000832', 'A machine or tool used by an operator to make measurements of specific properties of subjects or specimens.'),
       ('measurement_apparatus_software', 'Measurement apparatus software', 'IAO:0000010', 'Software that runs on a computer linked to a measurement apparatus to control the measurement process or extract data results.'),
       ('measurement_assay', 'Measurement assay', 'OBI:0500000', 'The plan design for the assessment of a subject or specimen for a specific feature. Usually the feature is quantitative. Usually the feature is also epistemologically elementary, as contrasted with assessments involving extensive reasoned judgement (as in a full-fledged diagnosis).'),
       ('method_of_marker_discretization', 'Method of marker discretization', 'STATO:0000213', 'The method by which the quantitative values of some property are cast into discrete values. For example, thresholding on the median over a collection.'),
       ('method_of_marker_quantification', 'Method of marker quantification', 'STATO:0000039', 'The method by which marker presence is quantified. For example, averaging of raster image intensity values over an image mask.'),
       ('name', 'Name', 'IAO:0000590', 'A symbol string meant to correspond to exactly one member of a collection, and generally also intended to be capable of verbalization in natural language speech or text.'),
       ('ordinality', 'Ordinality', 'OBCS:0000196', 'A data value that is an ordinal number, ie., a number that tells the position of something in a list.'),
       ('phenotypic_sex', 'Phenotypic sex', 'PATO:0000047', 'The class of reproductive compatibility to which a given organism belongs, in case its biological species admits such classes (gonochoric species). As indicated by observable phenotypic information. For example, male, female, or intersex.'),
       ('plane_coordinates_reference_system', 'Plane coordinates reference system', 'STATO:0000010', 'A correspondence between a specific two-dimensional material or spatial area (or class of such areas under specific conditions) and the standard two-dimensional coordinate space, in the special case of intrinsically-flat areas and correspondences which preserve distances up to an overall scale. Such a correspondence is determined uniquely by (i) a correspondence between just one reference point on the source and target, (ii) an indication of the direction of the first coordinate axis on the referent, (iii) the choice of one of the two possible directions of the remaining, second coordinate axis direction on the referent, and (iv) a choice of length scale, or unit.'),
       ('quantification_of_chemical_target_expression', 'Quantification of chemical target expression', 'OBI:0003142', 'An instance of determination of a quantity representing the amount of a chemical target present in a given specimen or structure, typically by means of a specific chemical marking ensemble rendering this amount as an observable quantity (e.g. immunofluoresence at a specific wavelength).'),
       ('quantitative_feature_derivation_process', 'Quantitative feature derivation process', '', 'An instance of quantification of a state or property of a subject which is carried out according to a given feature specification.'),
       ('specifier', 'Specifier', '', 'An identifier meant to be used in a limited context, for disambiguation between highly salient alternatives.'),
       ('statistical_test', 'Statistical test', 'OBI:0000673', 'See OBI.'),
       ('study_subject', 'Study subject', 'OBI:0000097', 'A person, other organism, or biospecimen which is the subject of some study.'),
       ('subspecimen_extraction_method', 'Subspecimen extraction method', 'OBI:0001882', 'The method by which subspecimens are extracted from a source specimen. For example, fine-needle aspiration.'),
       ('two_cohort_feature_association_test', 'Two-cohort feature association test', 'STATO:0000279', 'An application of a statistical test for association between a given specified feature on a sample set and assignment to one of two cohorts defined by selection criteria.'),
       ('unit', 'Unit', 'UO:0000000', 'For a 1-dimensional quantifiable/measurable property forming an abstract additive number system, i.e. exhibiting a natural addition operation, a unit is a choice of reference value for the property. Such a choice determines a correspondence between the possible values of the property and the standard 1-dimensional coordinate space, the (dimensionless) real numbers.'),
       ('investigation', 'Investigation', 'OBI:0000066', 'A planned process that consists of parts: planning, study design execution, documentation and which produce conclusion(s).'),
       ('study_contact_person', 'Study contact person', 'NCIT:C25461', 'A person who has responsibility for receiving general queries regarding the conduct of a given study.'),
       ('communication_contact_reference', 'Communication contact reference', 'NCIT:C70806', 'An address for direction of communication, e.g. an email address, a mailing address, or a phone number.'),
       ('study_component', 'Study component', 'BFO:0000050', 'A relation between a primary study and another study in which the latter is a component or part of the primary study.'),
       ('publication', 'Publication', 'IAO:0000312', 'A document, i.e. a collection of information content entities intended to be understood together as a whole, which is the output of a publishing process and which is about an investigation.'),
       ('publisher', 'Publisher', 'SIO:000885', 'The institution or organization which performs publication processes resulting in publications, i.e. which receives, accepts, and disseminates the document comprising the publications.'),
       ('author', 'Author', 'IAO:0000442', 'A person who performed a substantial amount of the writing of a given publication, or otherwise performed investigation and related work responsible for the substance of the publication.'),
       ('author_rank', 'Author rank', '', 'The position of an author in the rank order of authors advertised by the publisher of a given publication, typically decided by the authors as an indication of level of contribution, but sometimes decided by other means (e.g. alphabetical order on names). Often the author in first position declare responsibility for communication regarding the work.'),
       ('research_professional', 'Research professional', 'OBI:0000202', 'A person who performs research or a service that directly supports a research activity.'),
       ('personal_full_name', 'Personal full name', 'GSSO:001755', 'A full set of all personal names by which an individual is known and that can be recited as a word-group, with the understanding that, taken together, they all relate to that one individual.'),
       ('family_name', 'Family name', 'IAO:0020017', 'An identifier that is typically a part of a persons name which has been passed, according to law or custom, from one or both parents to their children.'),
       ('given_name', 'Given name', 'IAO:0020016', 'A personal name that specifies and differentiates between members of a group of individuals, especially in a family, all of whose members usually share the same family name (surname). A given name is purposefully given, usually by a childs parents at or near birth, in contrast to an inherited one such as a family name.'),
       ('open_researcher_and_contributor_identifier', 'Open researcher and contributor identifier', 'IAO:0000708', 'A centrally registered identifier that is issued by ORCID (https://orcid.org/) and used to persistently identify oneself as a human researcher or contributor.'),
       ('permanent_condition_diagnosis', 'Permanent condition diagnosis', '', 'A class of diagnoses for a specific condition for which a specific result indicates that a certain permanent effect has manifested in the subject. This can be either an inherently permanent effect (like death), or a synthetically permanent effect (like the subject has experienced a recurrence event at some point in the past, regarded as a state of the subject).'),
       ('condition_lack', 'Condition lack', '', 'The relation holding between two specific condition observations where the latter is precisely the observation of the lack of the former up to observation time.');

CREATE TABLE "reference_properties" (
"Name" TEXT,
  "Label" TEXT,
  "Entity" TEXT,
  "Value type" TEXT,
  "Related entity" TEXT,
  "Definitional reference" TEXT,
  "Definition" TEXT
);
INSERT INTO reference_properties VALUES ('assay_performer', 'Assay performer', 'Assay', 'String', '', 'OBI:0001950', 'The person or agent who performs a given assay.'),
       ('base64_file_contents', 'Base64 file contents', 'File', 'String', '', 'NCIT:C47879', 'The Base64-encoded ASCII character string serialization of the file contents byte string. The encoding is specified by RFC 4648.'),
       ('biospecimen_age_at_event', 'Biospecimen age at event', 'Biospecimen event', 'String', '', 'PATO:0000011', 'The amount of time between the inception of a given biospecimen (typically extraction) and the given event. Typically denominated in number of days.'),
       ('biospecimen_analyzed', 'Biospecimen analyzed', 'Analysis process', 'Entity', 'Biospecimen', '', 'The biospecimen analyzed by an analysis process, in case the subject is a biospecimen.'),
       ('biospecimen_storage_location', 'Biospecimen storage location', 'Biospecimen collection study', 'String', '', 'OBI:0302893', 'The location of storage of biospecimens during the period after collection but before measurement or analysis.'),
       ('cause_of_death', 'Cause of death', 'Study subject', 'String', '', 'OPMI:0000543', 'The most significant causative factor in the death of a given subject. Often but not always pertinent to the study of which the subject is a part, in the case of disease studies.'),
       ('cell_phenotype_criterion_marker', 'Cell phenotype criterion marker', 'Cell phenotype criterion', 'Entity', 'Chemical species', '', 'The chemical species whose presence or absence is the substance of a given cell phenotype criterion.'),
       ('cell_phenotype_criterion_polarity', 'Cell phenotype criterion polarity', 'Cell phenotype criterion', 'String', '', '', 'The value (typically positive or negative) stipulated by a given cell phenotype criterion.'),
       ('cell_phenotype_symbol', 'Cell phenotype symbol', 'Cell phenotype', 'String', '', '', 'A symbol string, not necessarily intended for verbalization in long-form speech or text, meant to summarize the intended meaning of a given cell phenotype. This is potentially an abbreviation of the full name.'),
       ('chemical_species_quantified', 'Chemical species quantified', 'Quantification of chemical target expression', 'Entity', 'Chemical species', '', 'The chemical species which is quantified by a given process.'),
       ('chemical_species_symbol', 'Chemical species symbol', 'Chemical species', 'String', '', '', 'A symbol string representation of the chemical species, or possibly a gene class of closely-related species (for example, BCL2 for a certain DNA segment, the corresponding mRNA molecule, and the corresponding protein product).'),
       ('component_study', 'Component study', 'Study component', 'Entity', 'Investigation', '', 'The component study of the component relation.'),
       ('condition_considered', 'Condition considered', 'Diagnosis event', 'String', '', 'BFO:0000016', 'The condition considered during a process of diagnosis.'),
       ('coordinate_system_orientation_specification', 'Coordinate system orientation specification', 'Plane coordinates reference system', 'String', '', 'PATO:0000133', 'The description of the direction, on the object or area of interest, intended to correspond to the first coordinate positive axis, plus a description of the choice of which of the two orthogonal directions is intended to correspond to the second coordinate positive axis.'),
       ('coordinate_system_reference_point', 'Coordinate system reference point', 'Plane coordinates reference system', 'String', '', 'NCIT:C45793', 'The description of a single point, on the object or area of focus, which serves as a reference point for establishing an orthogonal (Euclidean similarity) coordinate system.'),
       ('coordinate_system_reference_point_1', 'Coordinate system reference point 1', 'Plane coordinates reference system', 'Float', '', 'IAO:0000402', 'The intended first coordinate value of the coordinate-space point corresponding to the reference point. For orthogonal (Euclidean similarity) coordinate systems.'),
       ('coordinate_system_reference_point_2', 'Coordinate system reference point 2', 'Plane coordinates reference system', 'Float', '', 'IAO:0000402', 'The intended second coordinate value of the coordinate-space point corresponding to the reference point. For orthogonal (Euclidean similarity) coordinate systems.'),
       ('coordinate_system_unit', 'Coordinate system unit', 'Plane coordinates reference system', 'String', '', 'UO:0000001', 'A representation (e.g. 10 micrometers) of the length unit intended to correspond to the displacement in the coordinate space by the value 1. For orthogonal (Euclidean similarity) coordinate systems.'),
       ('data_file_generation_source_process', 'Data file generation source process', 'Data file', 'Entity', 'Biospecimen data measurement process', '', 'The measurement process which produced a given data file.'),
       ('date_of_birth', 'Date of birth', 'Study subject', 'Entity', 'Event date', 'UBERON:0035946', 'The date of inception, in the case of a biological subject.'),
       ('date_of_conclusion', 'Date of conclusion', 'Continuant', 'Entity', 'Event date', 'NCIT:C68617', 'The final date of the continuants existence.'),
       ('date_of_death', 'Date of death', 'Study subject', 'Entity', 'Event date', 'UBERON:0035944', 'The date of conclusion, in the case of a biological subject.'),
       ('date_of_diagnosis', 'Date of diagnosis', 'Diagnosis event', 'Entity', 'Event date', 'NCIT:C164339', 'The date on which a diagnosis was made.'),
       ('date_of_inception', 'Date of inception', 'Continuant', 'Entity', 'Event date', 'NCIT:C68616', 'The initial date of the continuants existence.'),
       ('date_of_intervention', 'Date of intervention', 'Intervention', 'Entity', 'Event date', 'NCIT:C80454', 'The date that a specific intervention was performed.'),
       ('date_of_publication', 'Date of publication', 'Publication', 'Entity', 'Event date', '', 'The date on which the publication process was completed.'),
       ('diagnosis_result', 'Diagnosis result', 'Diagnosis result', 'Entity', '', 'OGMS:0000073', 'The empirical claim about a subject supported by an act of diagnosis (often epistemologically complex and multi-factorial). May be positive or negative for disease presence, or an indication of disease subtype presence (e.g. triple-negative for the disease breast cancer).'),
       ('document_structure_class', 'Document structure class', 'Publication', 'String', '', 'IAO:0000310', 'See IAO.'),
       ('extracted_subspecimen', 'Extracted subspecimen', 'Biospecimen collection process', 'Entity', 'Biospecimen', '', 'The subspecimen extracted during a given biospecimen collection process.'),
       ('expression_quantity', 'Expression quantity', 'Quantification of chemical target expression', 'Float', '', 'NCIT:C25256', 'A real (dimensionless) numerical value representing an amount with respect to some unit.'),
       ('feature_subject', 'Feature subject', 'Quantitative feature derivation process', 'Entity', '', '', 'The entity that was subjected to the feature derivation or quantification process.'),
       ('feature_value', 'Feature value', 'Quantitative feature derivation process', 'Float', '', '', 'The quantity resulting from the quantification process.'),
       ('histological_structure_identification_performer', 'Histological structure identification performer', 'Histological structure identification process', 'String', '', 'OBI:0001950', 'The person who identified a histological structure or operated software making such an identification.'),
       ('institution_of_activity', 'Institution of activity', 'Investigation', 'Entity', 'Institution', 'OBI:0000828', 'The primary institution in which the investigation is carried out, which provides resources for the investigation, or which directs the conduct of the investigation.'),
       ('internet_reference', 'Internet reference', 'Publication', 'String', '', 'SIO:000811', 'A reference, typically a URL and often a DOI-formatted URL, that is issued by the publisher and refers to an at least partial digital representation of the publication.'),
       ('marking_antibody', 'Marking antibody', 'Biological marking system', 'String', '', '', 'The antibody used in the given marker/staining system.'),
       ('maximal_date_of_evidence', 'Maximal date of evidence', 'Evaluation', 'Entity', 'Event date', '', 'For an evaluation of activity or condition based on evidential factors of consideration, the most recent known date of creation of the evidence. If this date is accurately known, events after this date cannot bias the evaluation. For example, for a diagnosis based on a blood sample, X-rays, and a biopsy, if the blood sample was taken last, then the date of this sample is the maximal date of evidence.'),
       ('mechanism_of_target_marking', 'Mechanism of target marking', 'Biological marking system', 'String', '', 'OBI:0003146', 'The mechanism by which the given marker system renders the target antigen observable.'),
       ('primary_study', 'Primary study', 'Study component', 'Entity', 'Investigation', '', 'The primary study of the component relation.'),
       ('shape_specification_file_format', 'Shape specification file format', 'Coordinate shape specification', 'String', '', '', 'The documented file format for a given shape specification file.'),
       ('source_biospecimen', 'Source biospecimen', 'Biospecimen collection process', 'Entity', 'Biospecimen', '', 'The biospecimen from which a subspecimen was extracted during the given specimen collection process.'),
       ('specification_of_quantified_feature', 'Specification of quantified feature', 'Quantitative feature derivation process', 'Entity', 'Feature specification', '', 'The specification for feature derivation which was used to carry out a given instance of quantification.'),
       ('study_specifier', 'Study specifier', 'Investigation', 'Entity', 'Specifier', '', 'A short name for the study meant mainly for human-readable reference which disambiguates against other studies in the context of a single database instance.'),
       ('subject_of_quantification', 'Subject of quantification', 'Quantification of chemical target expression', 'Entity', 'Histological structure', '', 'The histological structure which is the domain for the given expression quantification process.'),
       ('subspecimen_extraction_site', 'Subspecimen extraction site', 'Biospecimen collection process', 'String', '', 'BFO:0000029', 'The location on the source specimen from which a subspecimen is extracted.'),
       ('test_probability_value', 'Test probability value', 'Two-cohort feature association test', 'Float', '', 'OBI:0000175', 'See OBI.');

CREATE TABLE "reference_values" (
"Name" TEXT,
  "Label" TEXT,
  "Enumeration" INTEGER,
  "Parent property" TEXT,
  "Definitional reference" TEXT,
  "Definition" TEXT
);
INSERT INTO reference_values VALUES ('positive', 'Positive', 0, 'Cell phenotype criterion polarity', 'CLO:0054406', 'For a binary/trinary cell phenotype criterion, the presence or most-abundance indicator.'),
       ('negative', 'Negative', 1, 'Cell phenotype criterion polarity', '', 'For a binary/trinary cell phenotype criterion, the absence or least-abundance indicator.'),
       ('low', 'Low', 2, 'Cell phenotype criterion polarity', '', 'For a trinary cell phenotype criterion, the intermediate value.'),
       ('immunohistochemistry', 'Immunohistochemistry', 0, 'Mechanism of target marking', 'OBI:0001986', 'An immunostaining assay to detect and potentially localize antigens within the cells of a tissue section. '),
       ('immunofluorescence', 'Immunofluorescence', 1, 'Mechanism of target marking', 'ECO:0000007', 'A marking system in which the antibody is conjugated to a fluorophore, the latter rendered observable by active imaging, the process consisting of excitation of the specimen and observation of emission at specific wavelengths.'),
       ('multiplexed_immunohistochemistry', 'Multiplexed immunohistochemistry', 2, 'Mechanism of target marking', '', 'Immunohistochemistry in which a special procedure is used to allow simultaneous or sequential staining on the same specimen.'),
       ('multiplexed_immunofluorescence', 'Multiplexed immunofluorescence', 3, 'Mechanism of target marking', 'OBI:0003091', 'Immunofluorescence in which a special procedure is used to allow simultaneous or sequential staining on the same specimen.'),
       ('in_situ_hybridization', 'In situ hybridization', 4, 'Mechanism of target marking', 'OBI:0001686', 'An assay that localizes a specific DNA or RNA sequence within a portion or section of tissue using artificially induced nucleic hybridization.'),
       ('fluorescence_in_situ_hybridization', 'Fluorescence in situ hybridization', 5, 'Mechanism of target marking', 'OBI:0003094', 'An in-situ hybridization assay in which fluorescently labeled molecules are used to localize specific DNA or RNA sequences.'),
       ('flow_cytometry', 'Flow cytometry', 6, 'Mechanism of target marking', 'OBI:0000916', 'A cytometry assay in which an input cell population is put in solution, is passed by a laser, and optical sensors are used to detect scattering of the laser light and/or fluorescence of specific markers to count and characterize the particles in solution.'),
       ('imaging_mass_cytometry', 'Imaging mass cytometry', 7, 'Mechanism of target marking', 'OBI:0003096', 'A cytometry time of flight assay in which molecules of interest on or in cells are imaged through a system in which samples are labeled with multiple different rare-earth tagged antibodies. The sample is then ablated with a laser and the labeled material is detected by cytometry time of flight mass spectrometry.'),
       ('esri_shapefile_shp', 'ESRI Shapefile SHP', 0, 'Shape specification file format', '', 'ESRI Shapefile .shp portion, feature geometry. Often the contents should be a single point or a single closed polygon.'),
       ('portable_network_graphics_mask', 'Portable network graphics mask', 1, 'Shape specification file format', 'NCIT:C85437', 'A Portable Network Graphics (PNG) file with 2-bit depth (monochrome). The 1 value indicates membership in the shape structure, and the 0 value indicates non-membership.'),
       ('viability', 'Viability', 0, 'Condition considered', 'PATO:0000169', 'An organismal quality inhering in a bearer or a population by virtue of the bearers disposition to survive.'),
       ('alive', 'Alive', 0, 'Diagnosis result', 'PATO:0001421', 'A viability quality inhering in a bearer by virtue of the bearers condition before death.'),
       ('article', 'Article', 0, 'Document structure class', 'NCIT:C47902', 'Nonfictional prose forming an independent part of a publication.'),
       ('dataset', 'Dataset', 1, 'Document structure class', 'T4FS:0000247', 'The release of research data, associated metadata, accompanying documentation, and software code (in cases where the raw data have been processed or manipulated) for re-use and analysis in such a manner that they can be discovered on the Web and referred to in a unique and persistent way. Data publishing occurs via dedicated data repositories.');
