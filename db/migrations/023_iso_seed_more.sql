-- Additional ISO27001:2022 controls to broaden the seed set
INSERT INTO controls (standard, ref, title, description)
SELECT *
FROM (VALUES
    ('ISO27001:2022', 'A.5.2', 'Information security roles and responsibilities', 'Define and allocate security responsibilities.'),
    ('ISO27001:2022', 'A.5.9', 'Inventory of information and other associated assets', 'Identify and maintain assets and owners.'),
    ('ISO27001:2022', 'A.5.10', 'Acceptable use of information and other associated assets', 'Define acceptable use rules.'),
    ('ISO27001:2022', 'A.5.13', 'Labeling of information', 'Label information according to classification.'),
    ('ISO27001:2022', 'A.5.18', 'Access rights', 'Provision, review, and removal of access rights.'),
    ('ISO27001:2022', 'A.7.4', 'Physical security monitoring', 'Monitor facilities to detect unauthorized access.'),
    ('ISO27001:2022', 'A.8.12', 'Data leakage prevention', 'Prevent unauthorized disclosure of information.'),
    ('ISO27001:2022', 'A.8.23', 'Web filtering', 'Manage web access to reduce exposure to threats.'),
    ('ISO27001:2022', 'A.8.28', 'Secure coding', 'Apply secure coding principles in development.'),
    ('ISO27001:2022', 'A.8.31', 'Separation of development, test and production environments', 'Isolate environments to reduce risk.'),
    ('ISO27001:2022', 'A.8.34', 'Protection of records', 'Protect records from loss, destruction, falsification, unauthorized access or release.'),
    ('ISO27001:2022', 'A.8.35', 'Privacy and protection of PII', 'Ensure privacy and PII protection aligned to laws and commitments.')
) AS seed(standard, ref, title, description)
ON CONFLICT (standard, ref) DO NOTHING;
