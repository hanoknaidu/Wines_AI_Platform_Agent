-- =============================================================================
-- Wines AI Platform Agent: seed data (FICTIONAL)
-- Every person, company, address, phone number, card token and wine in this
-- file is invented. Phone numbers use the reserved 555-01xx range, emails use
-- example.com/.net/.org. Real places (Hoboken, Napa, Pauillac) are used only
-- as geography. Reference "today" for the scenarios: 2026-11-19.
--
-- Monetary rule: base facts (unit prices, quantities, discounts) are written
-- here; derived money (line tax, totals, captures, refunds) is computed with
-- SQL below so every invariant holds by construction.
-- Tax rounding: half-up, (amount * rate_ppm + 500000) / 1000000 in integers.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Organization
-- -----------------------------------------------------------------------------
INSERT INTO stores (store_id, store_code, name, legal_name, state_code, license_type, license_number,
                    address_line1, city, postal_code, phone_e164, email, created_at, updated_at) VALUES
 (1, 'NJ-HOB', 'NJ Store (Hoboken)',  'Hudson Vine & Spirits NJ LLC', 'NJ', 'NJ Plenary Retail Distribution License', 'DEMO-NJ-PRD-0001',
     '418 Riverbend Avenue', 'Hoboken',  '07030', '+12015550101', 'nj-store@example.com', '2024-01-02T14:00:00Z', '2026-01-02T14:00:00Z'),
 (2, 'NY-CHE', 'NY Store (Chelsea)', 'Hudson Vine & Spirits NY Inc.', 'NY', 'NY SLA Retail Liquor Store License (L)', 'DEMO-NY-SLA-0001',
     '77 Vintner Row', 'New York', '10011', '+12125550102', 'ny-store@example.com', '2024-01-02T14:00:00Z', '2026-01-02T14:00:00Z');

-- A-80 / A-81 (0 = Sunday)
INSERT INTO store_hours (store_id, day_of_week, opens_at, closes_at) VALUES
 (1,0,'10:00','19:00'),(1,1,'09:00','22:00'),(1,2,'09:00','22:00'),(1,3,'09:00','22:00'),(1,4,'09:00','22:00'),(1,5,'09:00','22:00'),(1,6,'09:00','22:00'),
 (2,0,'10:00','20:00'),(2,1,'09:00','22:00'),(2,2,'09:00','22:00'),(2,3,'09:00','22:00'),(2,4,'09:00','22:00'),(2,5,'09:00','22:00'),(2,6,'09:00','22:00');

-- A-82
INSERT INTO store_hours_exceptions (store_id, exception_date, is_closed, opens_at, closes_at, note) VALUES
 (1,'2026-11-26',1,NULL,NULL,'Thanksgiving Day'),
 (2,'2026-11-26',1,NULL,NULL,'Thanksgiving Day'),
 (1,'2026-12-24',0,'09:00','18:00','Christmas Eve early close'),
 (2,'2026-12-24',0,'09:00','18:00','Christmas Eve early close'),
 (1,'2026-12-25',1,NULL,NULL,'Christmas Day'),
 (2,'2026-12-25',1,NULL,NULL,'Christmas Day (NY retail stores must close)'),
 (1,'2027-01-01',0,'12:00','18:00','New Year''s Day reduced hours'),
 (2,'2027-01-01',0,'12:00','18:00','New Year''s Day reduced hours');

INSERT INTO warehouses (warehouse_id, store_id, state_code, warehouse_code, name, warehouse_type,
                        is_pickup_point, ships_by_carrier, runs_local_delivery, address_line1, city, postal_code) VALUES
 (1, 1, 'NJ', 'NJ-HOB-FLOOR',  'Hoboken store floor & back room',       'store_floor',                  1, 0, 1, '418 Riverbend Avenue',   'Hoboken',          '07030'),
 (2, 1, 'NJ', 'NJ-SEC-FC',     'Secaucus fulfillment center',           'fulfillment_center',           0, 1, 1, '12 Meadowlands Parkway', 'Secaucus',         '07094'),
 (3, 2, 'NY', 'NY-CHE-FLOOR',  'Chelsea store floor & back room',       'store_floor',                  1, 0, 1, '77 Vintner Row',         'New York',         '10011'),
 (4, 2, 'NY', 'NY-LIC-FC',     'Long Island City fulfillment center',   'fulfillment_center',           0, 1, 1, '31-40 Skillman Way',     'Long Island City', '11101'),
 (5, 1, 'NJ', 'NJ-SEC-CELLAR', 'Secaucus temperature-controlled cellar','temperature_controlled_cellar',0, 1, 0, '12 Meadowlands Parkway', 'Secaucus',         '07094');

INSERT INTO staff_users (staff_id, employee_code, full_name, email, role, store_id, created_at) VALUES
 (1, 'S-1001', 'Dana Whitfield',     'dana.whitfield@staff.example.com',  'support_lead', NULL, '2024-02-01T14:00:00Z'),
 (2, 'S-1002', 'Marcus Oyelaran',    'marcus.oyelaran@staff.example.com', 'support_agent', NULL, '2024-03-11T14:00:00Z'),
 (3, 'S-1003', 'Priya Raman',        'priya.raman@staff.example.com',     'finance',      NULL, '2024-02-15T14:00:00Z'),
 (4, 'S-1004', 'Tomas Echeverria',   'tomas.echeverria@staff.example.com','fulfillment',  1,    '2024-01-15T14:00:00Z'),
 (5, 'S-1005', 'Grace Liu',          'grace.liu@staff.example.com',       'fulfillment',  2,    '2024-01-15T14:00:00Z'),
 (6, 'S-1006', 'Elena Kowalski',     'elena.kowalski@staff.example.com',  'compliance',   NULL, '2024-02-01T14:00:00Z'),
 (7, 'S-1007', 'Jordan Mbeki',       'jordan.mbeki@staff.example.com',    'pricing',      NULL, '2024-04-01T14:00:00Z'),
 (8, 'S-1008', 'Sam Adler',          'sam.adler@staff.example.com',       'catalog',      NULL, '2024-04-01T14:00:00Z');

-- -----------------------------------------------------------------------------
-- 2. Customers (all fictional)
-- -----------------------------------------------------------------------------
INSERT INTO customers (customer_id, customer_number, first_name, last_name, email, phone_e164, date_of_birth,
                       status, status_reason, home_store_id, marketing_source, last_login_at, created_at, updated_at) VALUES
 (1,  'C-100001','Olivia', 'Martinez',  'olivia.martinez@example.com',  '+12015550111','1986-04-12','active',NULL,1,'organic_search','2026-11-18T23:10:00Z','2025-03-02T15:20:00Z','2026-11-18T23:10:00Z'),
 (2,  'C-100002','James',  'Okafor',    'james.okafor@example.net',     '+12125550112','1979-09-30','active',NULL,2,'referral',      '2026-11-12T16:02:00Z','2025-05-19T19:45:00Z','2026-11-12T16:02:00Z'),
 (3,  'C-100003','Mei',    'Chen',      'mei.chen@example.org',         '+16095550113','1991-01-23','active',NULL,1,'paid_social',   '2026-11-14T01:30:00Z','2025-07-08T12:00:00Z','2026-11-14T01:30:00Z'),
 (4,  'C-100004','Daniel', 'Rosenberg', 'daniel.rosenberg@example.com', '+17185550114','1983-06-02','active',NULL,2,'email',         '2026-11-19T13:05:00Z','2025-09-14T21:10:00Z','2026-11-19T13:05:00Z'),
 (5,  'C-100005','Aisha',  'Rahman',    'aisha.rahman@example.net',     '+12015550115','1994-11-17','active',NULL,1,'organic_search','2026-11-18T18:40:00Z','2026-01-10T17:25:00Z','2026-11-18T18:40:00Z'),
 (6,  'C-100006','Robert', 'Fitzgerald','robert.fitzgerald@example.org','+19145550116','1962-02-08','active',NULL,2,'events',        '2026-11-10T14:00:00Z','2024-11-30T16:00:00Z','2026-11-10T14:00:00Z'),
 (7,  'C-100007','Sofia',  'Bianchi',   'sofia.bianchi@example.com',    '+19735550117','1988-08-21','active',NULL,1,'referral',      '2026-11-16T20:15:00Z','2024-12-12T18:30:00Z','2026-11-16T20:15:00Z'),
 (8,  'C-100008','William','Thompson',  'william.thompson@example.net', '+15165550118','1975-12-05','locked','Suspected account takeover: shipping address and email changed from new device; locked pending identity check (TKT-500005)',2,'organic_search','2026-11-17T03:12:00Z','2025-02-14T13:00:00Z','2026-11-17T04:05:00Z'),
 (9,  'C-100009','Hannah', 'Kim',       'hannah.kim@example.com',       '+12015550119','2004-10-03','active',NULL,1,'paid_social',   '2026-11-19T14:20:00Z','2026-11-18T22:00:00Z','2026-11-19T14:20:00Z'),
 (10, 'C-100010','Carlos', 'Mendes',    'carlos.mendes@example.org',    '+13475550120','1990-03-14','active',NULL,2,'organic_search','2026-11-02T22:45:00Z','2025-08-01T23:00:00Z','2026-11-02T22:45:00Z'),
 (11, 'C-100011','Emily',  'Novak',     'emily.novak@example.com',      '+17325550121','1982-07-29','active',NULL,1,'email',         '2026-11-17T15:00:00Z','2025-10-05T14:30:00Z','2026-11-17T15:00:00Z'),
 (12, 'C-100012','Michael','Brennan',   'michael.brennan@example.net',  '+16465550122','1970-05-19','active',NULL,2,'organic_search','2026-11-15T17:00:00Z','2025-04-22T20:00:00Z','2026-11-15T17:00:00Z');

INSERT INTO age_verifications (age_verification_id, customer_id, status, method, provider, provider_reference, failure_reason, started_at, completed_at) VALUES
 (1, 1,'verified','document_scan','IDV Provider (demo)','idv-demo-0001',NULL,'2025-03-02T15:22:00Z','2025-03-02T15:25:00Z'),
 (2, 2,'verified','database_check','IDV Provider (demo)','idv-demo-0002',NULL,'2025-05-19T19:46:00Z','2025-05-19T19:46:30Z'),
 (3, 3,'verified','document_scan','IDV Provider (demo)','idv-demo-0003',NULL,'2025-07-08T12:02:00Z','2025-07-08T12:06:00Z'),
 (4, 4,'verified','document_scan','IDV Provider (demo)','idv-demo-0004',NULL,'2025-09-14T21:12:00Z','2025-09-14T21:15:00Z'),
 (5, 5,'verified','database_check','IDV Provider (demo)','idv-demo-0005',NULL,'2026-01-10T17:26:00Z','2026-01-10T17:26:20Z'),
 (6, 6,'verified','in_person','Store ID check','NY-CHE-desk-0611',NULL,'2024-11-30T16:05:00Z','2024-11-30T16:06:00Z'),
 (7, 7,'verified','document_scan','IDV Provider (demo)','idv-demo-0007',NULL,'2024-12-12T18:31:00Z','2024-12-12T18:34:00Z'),
 (8, 8,'verified','database_check','IDV Provider (demo)','idv-demo-0008',NULL,'2025-02-14T13:01:00Z','2025-02-14T13:01:40Z'),
 (9, 9,'pending','document_scan','IDV Provider (demo)','idv-demo-0009',NULL,'2026-11-19T14:22:00Z',NULL),
 (10,10,'failed','document_scan','IDV Provider (demo)','idv-demo-0010','Photo glare: date of birth unreadable','2025-08-01T23:02:00Z','2025-08-01T23:04:00Z'),
 (11,10,'verified','document_scan','IDV Provider (demo)','idv-demo-0011',NULL,'2025-08-01T23:10:00Z','2025-08-01T23:13:00Z'),
 (12,11,'verified','database_check','IDV Provider (demo)','idv-demo-0012',NULL,'2025-10-05T14:31:00Z','2025-10-05T14:31:30Z'),
 (13,12,'manual_review','document_scan','IDV Provider (demo)','idv-demo-0013',NULL,'2025-04-22T20:02:00Z',NULL),
 (14,12,'verified','manual_review','Compliance team','manual-2025-0042',NULL,'2025-04-23T14:00:00Z','2025-04-23T15:30:00Z');

INSERT INTO customer_addresses (address_id, customer_id, label, recipient_name, line1, line2, city, state_code, postal_code, phone_e164,
                                address_type, delivery_instructions, is_default_shipping, is_default_billing, validated_at, created_at, updated_at, deleted_at) VALUES
 (1, 1,'Home',     'Olivia Martinez',  '25 Willowmere Street','Apt 4B','Hoboken','NJ','07030','+12015550111','residential','Buzz 4B; doorman until 9pm',1,1,'2025-03-02T15:30:00Z','2025-03-02T15:30:00Z','2025-03-02T15:30:00Z',NULL),
 (2, 1,'Office',   'Olivia Martinez',  '900 Harborview Plaza','Floor 12','Jersey City','NJ','07310','+12015550111','business','Front desk, weekdays only',0,0,'2025-06-11T13:00:00Z','2025-06-11T13:00:00Z','2025-06-11T13:00:00Z',NULL),
 (3, 2,'Home',     'James Okafor',     '140 Larkspur Avenue','Apt 9C','New York','NY','10011','+12125550112','residential',NULL,1,1,'2025-05-19T19:50:00Z','2025-05-19T19:50:00Z','2025-05-19T19:50:00Z',NULL),
 (4, 3,'Home',     'Mei Chen',         '61 Cedarbrook Lane',NULL,'Princeton','NJ','08540','+16095550113','residential','Side door',1,0,'2025-07-08T12:10:00Z','2025-07-08T12:10:00Z','2025-07-08T12:10:00Z',NULL),
 (5, 3,'Mailbox',  'Mei Chen',         'PO Box 3317',NULL,'Princeton','NJ','08542',NULL,'po_box',NULL,0,1,'2025-07-08T12:12:00Z','2025-07-08T12:12:00Z','2025-07-08T12:12:00Z',NULL),
 (6, 4,'Home',     'Daniel Rosenberg', '88 Fernhill Road','Unit 2','Brooklyn','NY','11215','+17185550114','residential','Ring twice',1,1,'2025-09-14T21:20:00Z','2025-09-14T21:20:00Z','2025-09-14T21:20:00Z',NULL),
 (7, 5,'Home',     'Aisha Rahman',     '310 Garnet Court','Apt 15A','Jersey City','NJ','07302','+12015550115','residential',NULL,1,1,'2026-01-10T17:30:00Z','2026-01-10T17:30:00Z','2026-01-10T17:30:00Z',NULL),
 (8, 6,'Home',     'Robert Fitzgerald','7 Hawthorne Ridge',NULL,'Scarsdale','NY','10583','+19145550116','residential','Gate code at front desk',1,0,'2024-11-30T16:10:00Z','2024-11-30T16:10:00Z','2024-11-30T16:10:00Z',NULL),
 (9, 6,'Billing',  'Robert Fitzgerald','42 Old Mill Lane',NULL,'Greenwich','CT','06830',NULL,'residential',NULL,0,1,'2024-11-30T16:12:00Z','2024-11-30T16:12:00Z','2024-11-30T16:12:00Z',NULL),
 (10,7,'Home',     'Sofia Bianchi',    '19 Orchard Terrace',NULL,'Montclair','NJ','07042','+19735550117','residential',NULL,1,1,'2024-12-12T18:40:00Z','2024-12-12T18:40:00Z','2024-12-12T18:40:00Z',NULL),
 (11,7,'Sister',   'Lucia Bianchi',    '5 Linden Hollow Drive',NULL,'Morristown','NJ','07960','+19735550127','residential','Gift recipient',0,0,'2025-12-01T15:00:00Z','2025-12-01T15:00:00Z','2025-12-01T15:00:00Z',NULL),
 (12,8,'Home',     'William Thompson', '23 Meadowbrook Road',NULL,'Garden City','NY','11530','+15165550118','residential',NULL,0,1,'2025-02-14T13:05:00Z','2025-02-14T13:05:00Z','2025-02-14T13:05:00Z',NULL),
 (13,8,'New (unverified)','W. Thompson','1450 Industrial Loop','Suite 9','Hempstead','NY','11550',NULL,'business','Added from new device 2026-11-17',1,0,NULL,'2026-11-17T03:20:00Z','2026-11-17T03:20:00Z',NULL),
 (14,9,'Home',     'Hannah Kim',       '62 Bloomfield Street','Apt 3','Hoboken','NJ','07030','+12015550119','residential',NULL,1,1,'2026-11-18T22:05:00Z','2026-11-18T22:05:00Z','2026-11-18T22:05:00Z',NULL),
 (15,10,'Home',    'Carlos Mendes',    '33-12 Ditmars Lane','Apt 5F','Astoria','NY','11105','+13475550120','residential','Call on arrival',1,1,'2025-08-01T23:20:00Z','2025-08-01T23:20:00Z','2025-08-01T23:20:00Z',NULL),
 (16,11,'Home',    'Emily Novak',      '14 Seabright Avenue',NULL,'Red Bank','NJ','07701','+17325550121','residential',NULL,1,1,'2025-10-05T14:35:00Z','2025-10-05T14:35:00Z','2025-10-05T14:35:00Z',NULL),
 (17,12,'Home',    'Michael Brennan',  '210 Gramercy Mews','Apt 7D','New York','NY','10010','+16465550122','residential',NULL,1,1,'2025-04-22T20:10:00Z','2025-04-22T20:10:00Z','2025-04-22T20:10:00Z',NULL),
 (18,2,'Old home', 'James Okafor',     '9 Stillwater Place',NULL,'Brooklyn','NY','11201',NULL,'residential',NULL,0,0,'2025-05-19T19:52:00Z','2025-05-19T19:52:00Z','2025-11-01T12:00:00Z','2025-11-01T12:00:00Z');

INSERT INTO customer_payment_methods (payment_method_id, customer_id, method_type, processor, processor_token, card_brand, card_last4,
                                      exp_month, exp_year, billing_address_id, is_default, status, created_at, removed_at) VALUES
 (1, 1,'card',      'card_gateway','tok_demo_9f2a11','visa',      '4411', 8,2028, 1,1,'active', '2025-03-02T15:40:00Z',NULL),
 (2, 1,'apple_pay', 'card_gateway','tok_demo_9f2a12','mastercard','7720',11,2027, 1,0,'active', '2025-11-20T18:00:00Z',NULL),
 (3, 2,'card',      'card_gateway','tok_demo_3c7b21','amex',      '1005', 4,2029, 3,1,'active', '2025-05-19T20:00:00Z',NULL),
 (4, 3,'card',      'card_gateway','tok_demo_51d031','mastercard','9910', 2,2028, 5,1,'active', '2025-07-08T12:20:00Z',NULL),
 (5, 4,'card',      'card_gateway','tok_demo_77e041','visa',      '2384', 6,2027, 6,1,'active', '2025-09-14T21:30:00Z',NULL),
 (6, 5,'google_pay','card_gateway','tok_demo_a1f051','visa',      '6602', 1,2029, 7,1,'active', '2026-01-10T17:40:00Z',NULL),
 (7, 6,'card',      'card_gateway','tok_demo_c4e061','amex',      '3007', 9,2028, 9,1,'active', '2024-11-30T16:20:00Z',NULL),
 (8, 7,'apple_pay', 'card_gateway','tok_demo_d2b071','visa',      '5150', 3,2028,10,1,'active', '2024-12-12T18:45:00Z',NULL),
 (9, 8,'card',      'card_gateway','tok_demo_e8a081','discover',  '6011',10,2027,12,1,'active', '2025-02-14T13:10:00Z',NULL),
 (10,9,'card',      'card_gateway','tok_demo_f3c091','visa',      '1881', 5,2030,14,1,'active', '2026-11-18T22:10:00Z',NULL),
 (11,10,'card',     'card_gateway','tok_demo_0b1101','mastercard','4520',12,2028,15,1,'active', '2025-08-01T23:30:00Z',NULL),
 (12,11,'card',     'card_gateway','tok_demo_1c2111','visa',      '7381', 7,2029,16,1,'active', '2025-10-05T14:40:00Z',NULL),
 (13,12,'card',     'card_gateway','tok_demo_2d3121','mastercard','8842', 3,2028,17,1,'active', '2025-04-22T20:20:00Z',NULL),
 (14,2,'card',      'card_gateway','tok_demo_3c7b22','visa',      '0157', 9,2025, 3,0,'removed','2025-05-19T20:05:00Z','2025-10-02T12:00:00Z');

INSERT INTO communication_preferences (customer_id, channel, purpose, is_opted_in, consent_source, consent_text_version, updated_at) VALUES
 (1,'email','marketing',1,'signup_form',NULL,'2025-03-02T15:20:00Z'),
 (1,'sms','marketing',1,'checkout','sms-consent-v3','2025-06-01T12:00:00Z'),
 (1,'sms','transactional',1,'default',NULL,'2025-03-02T15:20:00Z'),
 (2,'email','marketing',0,'account_settings',NULL,'2025-12-02T10:00:00Z'),
 (3,'email','marketing',1,'signup_form',NULL,'2025-07-08T12:00:00Z'),
 (4,'email','loyalty',1,'signup_form',NULL,'2025-09-14T21:10:00Z'),
 (5,'sms','marketing',0,'sms_keyword',NULL,'2026-05-03T16:00:00Z'),
 (6,'email','marketing',1,'support_request',NULL,'2025-01-15T15:00:00Z'),
 (7,'push','marketing',1,'account_settings',NULL,'2025-12-01T15:00:00Z'),
 (11,'email','marketing',0,'support_request',NULL,'2026-11-17T15:05:00Z');

INSERT INTO customer_taste_profiles (customer_id, preferred_sweetness, preferred_body, preferred_acidity, preferred_tannin, preferred_oak,
                                     preferred_fruit_profile, typical_budget_min_cents, typical_budget_max_cents, notes, updated_at) VALUES
 (1,'dry','light','crisp',NULL,'none','balanced',1500,3500,'Loves Sancerre and Chablis; mixed cases for dinner parties','2026-09-12T20:00:00Z'),
 (3,'dry','medium','fresh','smooth','subtle','earthy_savory',2000,5000,'Pinot Noir explorer','2026-11-02T18:00:00Z'),
 (4,'dry','full',NULL,'moderate','subtle','fruit_forward',2000,3500,'Kosher wines only','2025-09-14T21:30:00Z'),
 (5,'off_dry','light','fresh',NULL,'none','fruit_forward',1200,2500,'Prefers non-alcoholic and low-calorie options','2026-03-01T12:00:00Z'),
 (6,'dry','full',NULL,'grippy','pronounced','earthy_savory',6000,20000,'Collector: Bordeaux, Brunello, vintage Champagne','2026-10-05T14:00:00Z');

-- -----------------------------------------------------------------------------
-- 3. Catalog: geography, brands (fictional), grapes, styles, categories
-- -----------------------------------------------------------------------------
INSERT INTO regions (region_id, parent_region_id, name, region_level, country_code, appellation_system) VALUES
 (1,NULL,'France','country','FR',NULL),
 (2,NULL,'Italy','country','IT',NULL),
 (3,NULL,'United States','country','US',NULL),
 (4,NULL,'Spain','country','ES',NULL),
 (5,NULL,'New Zealand','country','NZ',NULL),
 (6,NULL,'Argentina','country','AR',NULL),
 (7,NULL,'Germany','country','DE',NULL),
 (8,NULL,'Portugal','country','PT',NULL),
 (9,NULL,'Israel','country','IL',NULL),
 (10,1,'Bordeaux','region','FR','AOC'),
 (11,10,'Pauillac','appellation','FR','AOC'),
 (12,1,'Loire Valley','region','FR','AOC'),
 (13,12,'Sancerre','appellation','FR','AOC'),
 (14,1,'Champagne','appellation','FR','AOC'),
 (15,1,'Burgundy','region','FR','AOC'),
 (16,15,'Chablis','appellation','FR','AOC'),
 (17,1,'Provence','region','FR','AOP'),
 (18,17,'Cotes de Provence','appellation','FR','AOP'),
 (19,2,'Tuscany','region','IT','DOC'),
 (20,19,'Chianti Classico','appellation','IT','DOCG'),
 (21,19,'Brunello di Montalcino','appellation','IT','DOCG'),
 (22,2,'Veneto','region','IT','DOC'),
 (23,22,'Prosecco','appellation','IT','DOC'),
 (24,2,'Piedmont','region','IT','DOC'),
 (25,24,'Barolo','appellation','IT','DOCG'),
 (26,3,'California','region','US','AVA'),
 (27,26,'Napa Valley','subregion','US','AVA'),
 (28,26,'Sonoma Coast','subregion','US','AVA'),
 (29,3,'Oregon','region','US','AVA'),
 (30,29,'Willamette Valley','subregion','US','AVA'),
 (31,3,'New York','region','US','AVA'),
 (32,31,'Finger Lakes','subregion','US','AVA'),
 (33,3,'New Jersey','region','US','AVA'),
 (34,33,'Outer Coastal Plain','subregion','US','AVA'),
 (35,4,'Rioja','appellation','ES','DOCa'),
 (36,5,'Marlborough','region','NZ','GI'),
 (37,6,'Mendoza','region','AR','GI'),
 (38,7,'Mosel','region','DE','PDO'),
 (39,8,'Douro','region','PT','DOC'),
 (40,39,'Porto','appellation','PT','DOC'),
 (41,9,'Galilee','region','IL','none'),
 (42,3,'Kentucky','region','US','none'),
 (43,NULL,'United Kingdom','country','GB',NULL),
 (44,43,'Speyside','region','GB','GI'),
 (45,NULL,'Mexico','country','MX',NULL),
 (46,45,'Jalisco','region','MX','GI');

INSERT INTO brands (brand_id, name, brand_type, home_region_id, founded_year, description) VALUES
 (1,'Chateau Lacoste-Merville','estate_winery',11,1878,'Left Bank classified-style estate (fictional)'),
 (2,'Domaine des Trois Collines','estate_winery',13,1952,'Family Sancerre grower (fictional)'),
 (3,'Maison Arnaud-Delcourt','champagne_house',14,1891,'Grower-negociant Champagne house (fictional)'),
 (4,'Domaine Vignot Freres','estate_winery',16,1965,'Chablis Premier Cru holdings (fictional)'),
 (5,'Chateau Sainte-Lumiere','estate_winery',18,1990,'Organic Provence rose estate (fictional)'),
 (6,'Fattoria Poggio Alto','estate_winery',20,1934,'Hillside Chianti Classico farm (fictional)'),
 (7,'Tenuta Val di Corvo','estate_winery',21,1971,'Montalcino estate (fictional)'),
 (8,'Cantina Colle Verde','cooperative',23,1958,'Prosecco cooperative (fictional)'),
 (9,'Cascina Rocca Bella','estate_winery',25,1920,'Barolo producer (fictional)'),
 (10,'Hollow Creek Cellars','estate_winery',27,1998,'Napa Valley Cabernet house (fictional)'),
 (11,'Coastline Ridge Wines','estate_winery',28,2004,'Cool-climate Sonoma Coast (fictional)'),
 (12,'Willow Bend Vineyards','estate_winery',30,1989,'Biodynamic Willamette estate (fictional)'),
 (13,'Seneca Shore Winery','estate_winery',32,1979,'Finger Lakes Riesling specialist (fictional)'),
 (14,'Pine Barrens Estate','estate_winery',34,2008,'South Jersey winery (fictional)'),
 (15,'Bodegas Monte Rojo','negociant',35,1902,'Rioja bodega (fictional)'),
 (16,'Tidewater Bay Wines','estate_winery',36,1996,'Marlborough producer (fictional)'),
 (17,'Altos del Viento','estate_winery',37,2001,'High-altitude Mendoza (fictional)'),
 (18,'Weingut Steinhof','estate_winery',38,1867,'Slate-slope Mosel estate (fictional)'),
 (19,'Quinta do Rio Alto','estate_winery',40,1850,'Douro Port house (fictional)'),
 (20,'Galil Heights Winery','estate_winery',41,1995,'Kosher Galilee winery (fictional)'),
 (21,'Clearleaf Zero','non_alcoholic_producer',7,2018,'Dealcoholized wines (fictional)'),
 (22,'Thin Line Wines','private_label',26,2020,'Lower-calorie wines (fictional)'),
 (23,'Old Lantern Distilling','distillery',42,2011,'Kentucky bourbon (fictional)'),
 (24,'Glen Aldair Distillery','distillery',44,1887,'Speyside single malt (fictional)'),
 (25,'Agave Sol Destileria','distillery',46,1999,'Highland Jalisco tequila (fictional)'),
 (26,'Hudson Vine Reserve','private_label',NULL,2024,'Store private label');

INSERT INTO grape_varieties (grape_id, name, skin_color, synonyms) VALUES
 (1,'Cabernet Sauvignon','red',NULL),(2,'Merlot','red',NULL),(3,'Petit Verdot','red',NULL),(4,'Sauvignon Blanc','white','Fume Blanc'),
 (5,'Chardonnay','white',NULL),(6,'Pinot Noir','red','Spatburgunder'),(7,'Pinot Meunier','red','Meunier'),(8,'Sangiovese','red','Brunello'),
 (9,'Nebbiolo','red',NULL),(10,'Glera','white',NULL),(11,'Tempranillo','red','Tinto Fino'),(12,'Malbec','red','Cot'),
 (13,'Riesling','white',NULL),(14,'Grenache','red','Garnacha'),(15,'Cinsault','red',NULL),(16,'Syrah','red','Shiraz'),
 (17,'Touriga Nacional','red',NULL),(18,'Chambourcin','red',NULL),(19,'Pinot Gris','pink','Pinot Grigio'),(20,'Cabernet Franc','red',NULL);

INSERT INTO wine_styles (style_code, display_name, description) VALUES
 ('light-crisp-white','Light & Crisp Whites','dry, light, crisp, no oak'),
 ('aromatic-white','Aromatic & Off-Dry Whites','dry to off-dry, light-medium, aromatic'),
 ('rich-white','Rich & Creamy Whites','dry, medium-full, subtle-pronounced oak'),
 ('rose-dry','Dry Rose','dry, light, fresh-crisp'),
 ('rose-off-dry','Sweet & Blush Rose','off-dry to medium sweet, light'),
 ('light-red','Light & Fruity Reds','dry, light, fresh, smooth tannin'),
 ('medium-red','Smooth & Medium Reds','dry, medium, smooth-moderate tannin'),
 ('bold-red','Bold & Structured Reds','dry, full, moderate-grippy tannin, often oaked'),
 ('sweet-red','Sweet Reds','off-dry to sweet, light-medium'),
 ('sparkling','Sparkling','varies; see sparkling sweetness scale'),
 ('dessert','Dessert Wines','sweet'),
 ('fortified','Fortified','Port, Sherry, Madeira'),
 ('orange','Orange / Skin-Contact','dry, medium, moderate tannin, earthy');

INSERT INTO categories (category_id, parent_category_id, slug, name, sort_order) VALUES
 (1,NULL,'wine','Wine',1),
 (2,1,'red-wine','Red Wine',1),(3,1,'white-wine','White Wine',2),(4,1,'rose-wine','Rose Wine',3),
 (5,1,'sparkling-wine','Sparkling Wine',4),(6,1,'dessert-and-fortified','Dessert & Fortified',5),
 (7,NULL,'non-alcoholic','Non-Alcoholic',2),
 (8,NULL,'spirits','Spirits',3),(9,8,'whiskey','Whiskey',1),(10,8,'tequila','Tequila',2),
 (11,NULL,'beer','Beer',4),
 (12,5,'champagne','Champagne',1),(13,5,'prosecco','Prosecco',2),
 (14,1,'organic-and-natural','Organic & Natural',6),(15,1,'kosher-wine','Kosher Wine',7),
 (16,1,'low-calorie-wine','Low-Calorie Wine',8),(17,1,'fine-and-rare','Fine & Rare',9);

-- -----------------------------------------------------------------------------
-- 4. Products and sellable variants (SKUs)
-- -----------------------------------------------------------------------------
INSERT INTO products (product_id, product_code, name, brand_id, product_type, wine_color, wine_type, style_code, region_id,
                      sweetness, body, acidity, tannin, oak, fruit_profile, sparkling_sweetness, closure_type,
                      description, tasting_notes, food_pairings, allergen_notes) VALUES
 (1,'P-0001','Chateau Lacoste-Merville Pauillac',1,'wine','red','still','bold-red',11,'dry','full','fresh','grippy','pronounced','balanced',NULL,'natural_cork','Cabernet-led Left Bank Bordeaux.','Cassis, cedar, graphite, firm tannins.','Ribeye, lamb, aged hard cheese','Contains sulfites; egg-white fining'),
 (2,'P-0002','Domaine des Trois Collines Sancerre',2,'wine','white','still','light-crisp-white',13,'dry','light','crisp',NULL,'none','balanced',NULL,'natural_cork','Flinty Loire Sauvignon Blanc.','Grapefruit, gooseberry, wet stone.','Goat cheese, oysters, salads','Contains sulfites'),
 (3,'P-0003','Maison Arnaud-Delcourt Brut Reserve',3,'wine','white','sparkling','sparkling',14,'dry','medium','crisp',NULL,'subtle','balanced','brut','natural_cork','Non-vintage house Champagne.','Brioche, green apple, lemon zest.','Fried chicken, sushi, celebrations','Contains sulfites'),
 (4,'P-0004','Maison Arnaud-Delcourt Millesime Brut',3,'wine','white','sparkling','sparkling',14,'dry','medium','crisp',NULL,'subtle','earthy_savory','brut','natural_cork','Vintage Champagne, aged 8+ years on lees.','Toasted hazelnut, honeyed citrus.','Lobster, truffle risotto','Contains sulfites'),
 (5,'P-0005','Domaine Vignot Freres Chablis',4,'wine','white','still','light-crisp-white',16,'dry','light','crisp',NULL,'none','earthy_savory',NULL,'natural_cork','Unoaked Burgundy Chardonnay.','Lemon, oyster shell, white flowers.','Shellfish, roast chicken','Contains sulfites'),
 (6,'P-0006','Chateau Sainte-Lumiere Cotes de Provence Rose',5,'wine','rose','still','rose-dry',18,'dry','light','fresh',NULL,'none','fruit_forward',NULL,'glass_stopper','Pale, dry Provence rose.','Strawberry, peach, herbs.','Salade nicoise, grilled fish','Contains sulfites; vegan'),
 (7,'P-0007','Fattoria Poggio Alto Chianti Classico',6,'wine','red','still','medium-red',20,'dry','medium','fresh','moderate','subtle','earthy_savory',NULL,'natural_cork','Organic Sangiovese.','Sour cherry, violet, dried herbs.','Pizza, pasta with red sauce','Contains sulfites'),
 (8,'P-0008','Tenuta Val di Corvo Brunello di Montalcino',7,'wine','red','still','bold-red',21,'dry','full','fresh','grippy','subtle','earthy_savory',NULL,'natural_cork','Limited allocation Brunello.','Dark cherry, leather, tobacco.','Bistecca, wild boar ragu','Contains sulfites'),
 (9,'P-0009','Cantina Colle Verde Prosecco Extra Dry',8,'wine','white','sparkling','sparkling',23,'off_dry','light','fresh',NULL,'none','fruit_forward','extra_dry','natural_cork','Charmat-method Prosecco.','Pear, green apple, acacia.','Brunch, mimosas, prosciutto','Contains sulfites'),
 (10,'P-0010','Cascina Rocca Bella Barolo',9,'wine','red','still','bold-red',25,'dry','full','crisp','grippy','subtle','earthy_savory',NULL,'natural_cork','Traditional Nebbiolo.','Rose, tar, red cherry.','Truffle pasta, braised beef','Contains sulfites'),
 (11,'P-0011','Hollow Creek Cellars Napa Valley Cabernet Sauvignon',10,'wine','red','still','bold-red',27,'dry','full','soft','moderate','pronounced','fruit_forward',NULL,'natural_cork','Ripe Napa Cabernet.','Blackberry, mocha, vanilla.','Burgers, steak','Contains sulfites'),
 (12,'P-0012','Coastline Ridge Sonoma Coast Chardonnay',11,'wine','white','still','rich-white',28,'dry','full','fresh',NULL,'pronounced','balanced',NULL,'natural_cork','Barrel-fermented Chardonnay.','Baked apple, butter, toasted oak.','Lobster roll, roast chicken','Contains sulfites'),
 (13,'P-0013','Coastline Ridge Sonoma Coast Pinot Noir',11,'wine','red','still','light-red',28,'dry','light','fresh','smooth','subtle','fruit_forward',NULL,'screw_cap','Cool-climate Pinot Noir.','Raspberry, cola, spice.','Salmon, mushrooms','Contains sulfites'),
 (14,'P-0014','Willow Bend Willamette Valley Pinot Noir',12,'wine','red','still','light-red',30,'dry','medium','fresh','smooth','subtle','earthy_savory',NULL,'natural_cork','Demeter-certified biodynamic Pinot Noir.','Cranberry, forest floor, clove.','Duck, mushroom risotto','Contains sulfites'),
 (15,'P-0015','Seneca Shore Finger Lakes Dry Riesling',13,'wine','white','still','aromatic-white',32,'dry','light','crisp',NULL,'none','fruit_forward',NULL,'screw_cap','Lake-effect cool-climate Riesling.','Lime, peach, slate.','Thai food, pork','Contains sulfites'),
 (16,'P-0016','Pine Barrens Estate Chambourcin',14,'wine','red','still','medium-red',34,'dry','medium','fresh','smooth','subtle','fruit_forward',NULL,'natural_cork','New Jersey hybrid red.','Plum, black pepper.','BBQ, pizza','Contains sulfites'),
 (17,'P-0017','Bodegas Monte Rojo Rioja Reserva',15,'wine','red','still','medium-red',35,'dry','medium','fresh','moderate','pronounced','balanced',NULL,'natural_cork','American-oak aged Tempranillo.','Strawberry, dill, vanilla.','Lamb chops, chorizo','Contains sulfites'),
 (18,'P-0018','Tidewater Bay Marlborough Sauvignon Blanc',16,'wine','white','still','light-crisp-white',36,'dry','light','crisp',NULL,'none','fruit_forward',NULL,'screw_cap','Zesty New Zealand Sauvignon Blanc.','Passion fruit, lime, cut grass.','Ceviche, goat cheese','Contains sulfites; vegan'),
 (19,'P-0019','Altos del Viento Malbec',17,'wine','red','still','bold-red',37,'dry','full','soft','smooth','subtle','fruit_forward',NULL,'natural_cork','Everyday high-altitude Malbec.','Plum, violet, cocoa.','Grilled meats, empanadas','Contains sulfites'),
 (20,'P-0020','Weingut Steinhof Mosel Riesling Kabinett',18,'wine','white','still','aromatic-white',38,'off_dry','light','crisp',NULL,'none','fruit_forward',NULL,'screw_cap','Low-alcohol off-dry Kabinett.','Green apple, honeysuckle, slate.','Spicy Asian dishes','Contains sulfites'),
 (21,'P-0021','Quinta do Rio Alto 20 Year Old Tawny Port',19,'wine','red','fortified','fortified',40,'sweet','full','fresh',NULL,'pronounced','balanced',NULL,'glass_stopper','Aged tawny Port.','Caramel, walnut, dried fig.','Creme brulee, blue cheese','Contains sulfites'),
 (22,'P-0022','Galil Heights Cabernet Sauvignon',20,'wine','red','still','bold-red',41,'dry','full','fresh','moderate','subtle','fruit_forward',NULL,'natural_cork','Kosher, mevushal Galilee Cabernet.','Black cherry, Mediterranean herbs.','Brisket, lamb','Contains sulfites'),
 (23,'P-0023','Clearleaf Zero Sparkling Rose',21,'non_alcoholic_wine','rose','sparkling','sparkling',7,'off_dry','light','fresh',NULL,'none','fruit_forward','dry','crown_cap','Dealcoholized sparkling rose, under 0.5% ABV.','Red berries, citrus.','Brunch, celebrations','Contains sulfites'),
 (24,'P-0024','Clearleaf Zero Riesling',21,'non_alcoholic_wine','white','still','aromatic-white',7,'off_dry','light','fresh',NULL,'none','fruit_forward',NULL,'screw_cap','Dealcoholized Riesling.','Apricot, lime.','Salads, sushi','Contains sulfites'),
 (25,'P-0025','Thin Line Sauvignon Blanc',22,'wine','white','still','light-crisp-white',26,'dry','light','crisp',NULL,'none','fruit_forward',NULL,'screw_cap','Lower-alcohol, lower-calorie white.','Lemon, melon.','Light salads','Contains sulfites'),
 (26,'P-0026','Old Lantern Small Batch Bourbon',23,'spirit',NULL,NULL,NULL,42,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'natural_cork','Small-batch Kentucky straight bourbon.','Caramel, baking spice, oak.',NULL,NULL),
 (27,'P-0027','Glen Aldair 12 Year Old Single Malt',24,'spirit',NULL,NULL,NULL,44,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'natural_cork','Speyside single malt Scotch.','Honey, orchard fruit, malt.',NULL,NULL),
 (28,'P-0028','Agave Sol Blanco Tequila',25,'spirit',NULL,NULL,NULL,46,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'natural_cork','100% blue Weber agave blanco.','Cooked agave, citrus, pepper.',NULL,NULL),
 (29,'P-0029','Hudson Vine Reserve Hazy IPA',26,'beer',NULL,NULL,NULL,33,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'none','Private-label NJ-brewed hazy IPA.','Mango, citrus, soft bitterness.',NULL,'Contains gluten (barley)');

INSERT INTO product_categories (product_id, category_id, is_primary) VALUES
 (1,2,1),(1,17,0),(2,3,1),(3,12,1),(4,12,1),(4,17,0),(5,3,1),(6,4,1),(6,14,0),(7,2,1),(7,14,0),(8,2,1),(8,17,0),(9,13,1),
 (10,2,1),(10,17,0),(11,2,1),(12,3,1),(13,2,1),(14,2,1),(14,14,0),(15,3,1),(16,2,1),(17,2,1),(18,3,1),(19,2,1),(20,3,1),
 (21,6,1),(22,2,1),(22,15,0),(23,7,1),(24,7,1),(25,3,1),(25,16,0),(26,9,1),(27,9,1),(28,10,1),(29,11,1);

INSERT INTO product_grapes (product_id, grape_id, percentage) VALUES
 (1,1,70),(1,2,25),(1,3,5),(2,4,100),(3,5,40),(3,6,35),(3,7,25),(4,5,60),(4,6,40),(5,5,100),(6,14,50),(6,15,30),(6,16,20),
 (7,8,95),(8,8,100),(9,10,100),(10,9,100),(11,1,88),(11,2,12),(12,5,100),(13,6,100),(14,6,100),(15,13,100),(16,18,100),
 (17,11,90),(17,14,NULL),(18,4,100),(19,12,100),(20,13,100),(21,17,NULL),(22,1,100),(23,6,NULL),(23,5,NULL),(24,13,100),(25,4,100);

INSERT INTO product_variants (variant_id, product_id, sku, gtin, vintage_year, size_ml, pack_quantity, container_type, abv_percent,
                              is_vintage_specific, is_collectible, is_final_sale, case_discount_eligible, weight_grams, status) VALUES
 (1, 1,'WN-LCM-PAU-2019-750',  '0000000100014',2019, 750,1,'bottle',13.5,1,0,0,1,1450,'active'),
 (2, 1,'WN-LCM-PAU-2020-750',  '0000000100021',2020, 750,1,'bottle',13.5,1,0,0,1,1450,'active'),
 (3, 1,'WN-LCM-PAU-2015-1500', '0000000100038',2015,1500,1,'bottle',13.0,1,1,1,0,2900,'active'),
 (4, 2,'WN-TCO-SAN-2023-750',  '0000000100045',2023, 750,1,'bottle',12.5,0,0,0,1,1300,'active'),
 (5, 2,'WN-TCO-SAN-2024-750',  '0000000100052',2024, 750,1,'bottle',12.5,0,0,0,1,1300,'active'),
 (6, 2,'WN-TCO-SAN-2023-375',  '0000000100069',2023, 375,1,'bottle',12.5,0,0,0,1, 700,'active'),
 (7, 3,'WN-ARD-BRT-NV-750',    '0000000100076',NULL, 750,1,'bottle',12.0,0,0,0,1,1650,'active'),
 (8, 3,'WN-ARD-BRT-NV-1500',   '0000000100083',NULL,1500,1,'bottle',12.0,0,0,0,1,3100,'active'),
 (9, 3,'WN-ARD-BRT-NV-375',    '0000000100090',NULL, 375,1,'bottle',12.0,0,0,0,1, 850,'active'),
 (10,4,'WN-ARD-MIL-2015-750',  '0000000100106',2015, 750,1,'bottle',12.5,1,1,0,0,1650,'active'),
 (11,5,'WN-VGF-CHB-2022-750',  '0000000100113',2022, 750,1,'bottle',12.5,0,0,0,1,1300,'active'),
 (12,6,'WN-STL-CDP-2025-750',  '0000000100120',2025, 750,1,'bottle',13.0,0,0,0,1,1350,'active'),
 (13,6,'WN-STL-CDP-2025-1500', '0000000100137',2025,1500,1,'bottle',13.0,0,0,0,1,2700,'active'),
 (14,7,'WN-FPA-CCL-2021-750',  '0000000100144',2021, 750,1,'bottle',13.5,0,0,0,1,1300,'active'),
 (15,7,'WN-FPA-CCL-2022-750',  '0000000100151',2022, 750,1,'bottle',13.5,0,0,0,1,1300,'coming_soon'),
 (16,8,'WN-VDC-BRU-2019-750',  '0000000100168',2019, 750,1,'bottle',14.5,1,0,0,0,1450,'active'),
 (17,9,'WN-CCV-PRO-NV-750',    '0000000100175',NULL, 750,1,'bottle',11.0,0,0,0,1,1550,'active'),
 (18,9,'WN-CCV-PRO-NV-187X4',  '0000000100182',NULL, 187,4,'bottle',11.0,0,0,0,1,1500,'active'),
 (19,10,'WN-CRB-BAR-2020-750', '0000000100199',2020, 750,1,'bottle',14.0,1,0,0,1,1450,'active'),
 (20,11,'WN-HCC-NCS-2022-750', '0000000100205',2022, 750,1,'bottle',14.5,0,0,0,1,1450,'active'),
 (21,11,'WN-HCC-NCS-2021-750', '0000000100212',2021, 750,1,'bottle',14.5,0,0,0,1,1450,'discontinued'),
 (22,12,'WN-CRW-SCC-2023-750', '0000000100229',2023, 750,1,'bottle',13.8,0,0,0,1,1350,'active'),
 (23,13,'WN-CRW-SCP-2023-750', '0000000100236',2023, 750,1,'bottle',13.2,0,0,0,1,1350,'active'),
 (24,14,'WN-WBV-WPN-2022-750', '0000000100243',2022, 750,1,'bottle',13.0,0,0,0,1,1350,'active'),
 (25,15,'WN-SSW-FDR-2024-750', '0000000100250',2024, 750,1,'bottle',11.8,0,0,0,1,1300,'active'),
 (26,16,'WN-PBE-CHA-2023-750', '0000000100267',2023, 750,1,'bottle',12.8,0,0,0,1,1300,'active'),
 (27,17,'WN-BMR-RIO-2019-750', '0000000100274',2019, 750,1,'bottle',14.0,0,0,0,1,1400,'active'),
 (28,18,'WN-TBW-MSB-2025-750', '0000000100281',2025, 750,1,'bottle',13.0,0,0,0,1,1250,'active'),
 (29,19,'WN-ADV-MAL-2023-750', '0000000100298',2023, 750,1,'bottle',13.9,0,0,0,1,1300,'active'),
 (30,20,'WN-WST-MRK-2023-750', '0000000100304',2023, 750,1,'bottle', 8.5,0,0,0,1,1300,'active'),
 (31,21,'WN-QRA-T20-NV-750',   '0000000100311',NULL, 750,1,'bottle',20.0,0,0,0,1,1500,'active'),
 (32,22,'WN-GHW-CAB-2022-750', '0000000100328',2022, 750,1,'bottle',14.0,0,0,0,1,1400,'active'),
 (33,23,'NA-CLZ-SPR-NV-750',   '0000000100335',NULL, 750,1,'bottle', 0.0,0,0,0,0,1500,'active'),
 (34,24,'NA-CLZ-RIE-NV-750',   '0000000100342',NULL, 750,1,'bottle', 0.4,0,0,0,0,1250,'active'),
 (35,25,'WN-TLW-SBL-2025-750', '0000000100359',2025, 750,1,'bottle', 9.0,0,0,0,1,1250,'active'),
 (36,26,'SP-OLD-BBN-NV-750',   '0000000100366',NULL, 750,1,'bottle',47.5,0,0,0,0,1300,'active'),
 (37,27,'SP-GLA-12Y-NV-750',   '0000000100373',NULL, 750,1,'bottle',43.0,0,0,0,0,1350,'active'),
 (38,28,'SP-ASL-BLA-NV-750',   '0000000100380',NULL, 750,1,'bottle',40.0,0,0,0,0,1300,'active'),
 (39,29,'BR-HVR-IPA-NV-355X6', '0000000100397',NULL, 355,6,'can',    6.8,0,0,0,0,2300,'active');

INSERT INTO variant_certifications (variant_id, certification_type, evidence_level, certifier, evidence_ref, verified_at, expires_at, status) VALUES
 (12,'eu_organic','certified','Ecocert (demo)','CERT-DEMO-STL-2025','2026-03-02T15:00:00Z','2027-03-01T00:00:00Z','active'),
 (13,'eu_organic','certified','Ecocert (demo)','CERT-DEMO-STL-2025','2026-03-02T15:00:00Z','2027-03-01T00:00:00Z','active'),
 (12,'vegan','declared',NULL,'DECL-DEMO-STL-FINING','2026-03-02T15:00:00Z',NULL,'active'),
 (14,'eu_organic','certified','ICEA (demo)','CERT-DEMO-FPA-2021','2025-10-01T15:00:00Z','2026-09-30T00:00:00Z','expired'),
 (15,'eu_organic','certified','ICEA (demo)','CERT-DEMO-FPA-2022','2026-10-15T15:00:00Z','2027-10-14T00:00:00Z','active'),
 (24,'demeter','certified','Demeter USA (demo)','CERT-DEMO-WBV-2022','2026-02-10T15:00:00Z','2027-02-09T00:00:00Z','active'),
 (24,'live','certified','LIVE (demo)','CERT-DEMO-WBV-LIVE','2026-02-10T15:00:00Z','2027-02-09T00:00:00Z','active'),
 (28,'swnz','certified','SWNZ (demo)','CERT-DEMO-TBW-2025','2026-04-01T15:00:00Z',NULL,'active'),
 (28,'vegan','declared',NULL,'DECL-DEMO-TBW-FINING','2026-04-01T15:00:00Z',NULL,'active'),
 (32,'kosher','certified','OU (demo)','HECHSHER-DEMO-GHW-2022','2025-12-01T15:00:00Z',NULL,'active'),
 (32,'mevushal','certified','OU (demo)','HECHSHER-DEMO-GHW-2022','2025-12-01T15:00:00Z',NULL,'active'),
 (7,'practicing_organic','declared',NULL,'DECL-DEMO-ARD-VINEYARD','2026-01-15T15:00:00Z',NULL,'active');

INSERT INTO variant_nutrition (variant_id, serving_ml, calories, carbs_g, sugar_g, residual_sugar_g_per_l, source, verified_at) VALUES
 (35,150, 85,2.5,0.6,  1.0,'producer_tech_sheet','2026-05-10T15:00:00Z'),
 (33,150, 30,7.0,6.5, 40.0,'label','2026-04-02T15:00:00Z'),
 (34,150, 25,6.0,5.5, 35.0,'label','2026-04-02T15:00:00Z'),
 (28,150,120,3.0,0.9,  2.5,'lab_analysis','2026-04-01T15:00:00Z'),
 (30,150,110,9.0,7.5, 45.0,'producer_tech_sheet','2026-02-01T15:00:00Z'),
 (17,150,115,4.0,2.4, 14.0,'producer_tech_sheet','2026-01-20T15:00:00Z');

-- Publication names are fictional on purpose (no invented scores attributed to real critics).
INSERT INTO product_accolades (accolade_id, variant_id, source, score, award, awarded_year) VALUES
 (1, 1,'Atlantic Wine Review',95,NULL,2022),
 (2,16,'Atlantic Wine Review',96,NULL,2024),
 (3,16,'Cellar Notes Quarterly',94,NULL,2024),
 (4,10,'Cellar Notes Quarterly',97,NULL,2023),
 (5,24,'Pacific Cellar Journal',93,NULL,2024),
 (6,25,'Great Lakes Wine Competition (demo)',NULL,'Double Gold',2025),
 (7,26,'Garden State Wine Awards (demo)',NULL,'Best Red Hybrid',2025);

-- -----------------------------------------------------------------------------
-- 5. Listings per store (assortment, jurisdiction, allocation) - A-03, A-06
-- -----------------------------------------------------------------------------
INSERT INTO product_listings (store_id, variant_id, created_at, updated_at)
SELECT s.store_id, v.variant_id, '2026-01-01T05:00:00Z', '2026-01-01T05:00:00Z'
FROM stores s CROSS JOIN product_variants v
WHERE NOT (s.store_id = 2 AND v.variant_id IN (3, 26));   -- NJ-only: cellar magnum, NJ Chambourcin

UPDATE product_listings SET listing_status = 'coming_soon', next_arrival_estimate = '2026-12-05' WHERE variant_id = 15;
UPDATE product_listings SET listing_status = 'discontinued' WHERE variant_id = 21;
UPDATE product_listings SET allocation_limit = 2 WHERE store_id = 1 AND variant_id = 16;
UPDATE product_listings SET listing_status = 'pre_arrival', next_arrival_estimate = '2027-02-15' WHERE store_id = 2 AND variant_id = 10;
UPDATE product_listings SET listing_status = 'special_order' WHERE store_id = 2 AND variant_id = 31;
UPDATE product_listings SET listing_status = 'temporarily_unavailable' WHERE store_id = 2 AND variant_id = 19;
UPDATE product_listings SET listing_status = 'in_store_only' WHERE store_id = 2 AND variant_id = 39;
UPDATE product_listings SET backorder_allowed = 1, next_arrival_estimate = '2026-12-01' WHERE store_id = 2 AND variant_id = 13;
UPDATE product_listings SET next_arrival_estimate = '2026-11-28' WHERE store_id = 2 AND variant_id = 29;
UPDATE product_listings SET is_sellable = 0,
       not_sellable_reason = 'A-06: non-alcoholic wine is sold by the NJ Store only until NY compliance review (Q-1)'
 WHERE store_id = 2 AND variant_id IN (33, 34);
UPDATE product_listings SET max_per_order = 6 WHERE variant_id IN (3, 10);

-- -----------------------------------------------------------------------------
-- 6. Prices (effective-dated). Current regular price ids: NJ = 1000 + variant,
--    NY = 2000 + variant. History and sale rows use 5000+.
-- -----------------------------------------------------------------------------
WITH p(variant_id, nj, ny) AS (VALUES
 (1,9500,9900),(2,8900,9300),(3,26000,NULL),(4,3200,3400),(5,3400,3600),(6,1800,1900),(7,5800,6100),(8,12500,12900),
 (9,3100,3300),(10,14000,14800),(11,2900,3100),(12,2200,2400),(13,4800,5100),(14,2400,2600),(15,2500,2700),(16,7200,7600),
 (17,1600,1700),(18,2200,2300),(19,6500,6800),(20,4800,5000),(21,4600,4800),(22,2800,2900),(23,3500,3700),(24,4200,4400),
 (25,1900,2000),(26,2100,NULL),(27,2700,2900),(28,1500,1600),(29,1400,1500),(30,2300,2400),(31,6500,6900),(32,2600,2700),
 (33,1800,1900),(34,1400,1500),(35,1700,1800),(36,4200,4500),(37,6800,7200),(38,3900,4200),(39,1400,1500))
INSERT INTO product_prices (price_id, store_id, variant_id, price_type, amount_cents, starts_at, ends_at, change_reason, created_by_staff_id, created_at)
SELECT 1000 + variant_id, 1, variant_id, 'regular', nj,
       CASE variant_id WHEN 20 THEN '2026-03-01T05:00:00Z' ELSE '2026-01-01T05:00:00Z' END,
       NULL, CASE variant_id WHEN 20 THEN 'Distributor cost increase' ELSE '2026 price file' END, 7, '2025-12-20T15:00:00Z'
FROM p
UNION ALL
SELECT 2000 + variant_id, 2, variant_id, 'regular', ny, '2026-01-01T05:00:00Z', NULL, '2026 price file', 7, '2025-12-20T15:00:00Z'
FROM p WHERE ny IS NOT NULL;

INSERT INTO product_prices (price_id, store_id, variant_id, price_type, amount_cents, compare_at_cents, compare_at_verified,
                            starts_at, ends_at, change_reason, created_by_staff_id, created_at) VALUES
 (5001,1,20,'regular',4500,NULL,0,'2025-06-01T04:00:00Z','2026-03-01T05:00:00Z','2025 price file',7,'2025-05-20T15:00:00Z'),
 (5002,1,27,'sale',   2299,2700,1,'2026-11-01T04:00:00Z','2026-12-01T05:00:00Z','November Rioja feature',7,'2026-10-25T15:00:00Z'),
 (5003,1, 7,'sale',   5299,5800,1,'2026-11-15T05:00:00Z','2027-01-02T05:00:00Z','Holiday Champagne sale',7,'2026-11-10T15:00:00Z'),
 (5004,2, 7,'sale',   5599,6100,1,'2026-11-15T05:00:00Z','2027-01-02T05:00:00Z','Holiday Champagne sale',7,'2026-11-10T15:00:00Z'),
 (5005,1,17,'sale',   1399,1600,1,'2026-09-01T04:00:00Z','2026-10-01T04:00:00Z','Labor Day Prosecco sale',7,'2026-08-25T15:00:00Z'),
 (5006,2,12,'sale',   1999,2400,1,'2026-06-01T04:00:00Z','2026-09-01T04:00:00Z','Summer rose sale',7,'2026-05-25T15:00:00Z');

-- Internal landed cost (~62% of shelf) for the below-cost floor (A-54).
INSERT INTO product_costs (store_id, variant_id, unit_cost_cents, effective_from, source)
SELECT store_id, variant_id, amount_cents * 62 / 100, '2026-01-01T05:00:00Z', 'distributor_invoice'
FROM product_prices WHERE price_type = 'regular' AND ends_at IS NULL;

-- Illustrative rates (the tax engine is authoritative; verify before production use).
INSERT INTO tax_rates (tax_rate_id, state_code, jurisdiction_name, postal_code, rate_ppm, applies_to_shipping, effective_from) VALUES
 (1,'NJ','New Jersey (statewide)',NULL,66250,1,'2018-01-01'),
 (2,'NY','New York City',NULL,88750,1,'2009-08-01'),
 (3,'NY','Nassau County',NULL,86250,1,'2009-08-01'),
 (4,'NY','Westchester County (outside cities)',NULL,83750,1,'2023-08-01');

-- A-10..A-16
INSERT INTO fulfillment_rates (rate_id, store_id, fulfillment_type, zone, min_distance_miles, max_distance_miles, min_bottles, max_bottles,
                               fee_cents, extra_fee_per_6_bottles_cents, order_minimum_cents, free_threshold_cents, effective_from) VALUES
 (1,1,'local_delivery',1, 0, 5,NULL,NULL, 599,  0,4000, 9900,'2026-01-01'),
 (2,1,'local_delivery',2, 5,15,NULL,NULL, 999,  0,4000, 9900,'2026-01-01'),
 (3,1,'pickup',NULL,NULL,NULL,NULL,NULL,     0,  0,   0, NULL,'2026-01-01'),
 (4,1,'shipping',NULL,NULL,NULL,1,6,      1499,  0,   0,19900,'2026-01-01'),
 (5,1,'shipping',NULL,NULL,NULL,7,12,     1999,500,   0,19900,'2026-01-01'),
 (6,2,'local_delivery',1, 0, 5,NULL,NULL, 599,  0,4000, 9900,'2026-01-01'),
 (7,2,'local_delivery',2, 5,15,NULL,NULL, 999,  0,4000, 9900,'2026-01-01'),
 (8,2,'pickup',NULL,NULL,NULL,NULL,NULL,     0,  0,   0, NULL,'2026-01-01'),
 (9,2,'shipping',NULL,NULL,NULL,1,6,      1499,  0,   0,19900,'2026-01-01'),
 (10,2,'shipping',NULL,NULL,NULL,7,12,    1999,500,   0,19900,'2026-01-01');

-- -----------------------------------------------------------------------------
-- 7. Promotions (A-50..A-53)
-- -----------------------------------------------------------------------------
INSERT INTO promotions (promotion_id, code, name, promo_type, percent_off_bps, amount_off_cents, min_subtotal_cents, store_id,
                        is_stackable, max_redemptions, max_per_customer, starts_at, ends_at, status, terms, created_at) VALUES
 (1,NULL,'Mixed Case Discount','mixed_case',NULL,NULL,0,NULL,0,NULL,NULL,'2025-01-01T05:00:00Z',NULL,'active',
    '10% off 6-11 eligible 750 ml-equivalent wines, 15% off 12+. Excludes allocated, collectible, pre-arrival, special-order, NA and price-matched items.','2024-12-15T15:00:00Z'),
 (2,'WELCOME10','First order $10 off','first_order',NULL,1000,7500,NULL,0,NULL,1,'2025-01-01T05:00:00Z',NULL,'active',
    '$10 off a first order of $75+ product subtotal; one per person, household and payment method.','2024-12-15T15:00:00Z'),
 (3,'FALL10','Fall 10% off','percent_off',1000,NULL,5000,NULL,0,5000,1,'2026-10-01T04:00:00Z','2026-12-01T05:00:00Z','active',
    '10% off wine orders of $50+. Not valid on Fine & Rare. Does not combine with the mixed-case discount.','2026-09-20T15:00:00Z'),
 (4,'FREEDELIVERY','Free local delivery (NJ)','free_delivery',NULL,NULL,6000,1,1,NULL,1,'2026-11-01T04:00:00Z','2026-12-01T05:00:00Z','active',
    'Free local delivery from the NJ Store on orders of $60+.','2026-10-25T15:00:00Z'),
 (5,NULL,'Rewards $10 reward','loyalty_reward',NULL,1000,0,NULL,1,NULL,NULL,'2025-01-01T05:00:00Z',NULL,'active',
    '250 points = $10 reward, valid 90 days.','2024-12-15T15:00:00Z'),
 (6,'SUMMERROSE','Summer rose 20% off','percent_off',2000,NULL,0,NULL,0,NULL,1,'2026-06-01T04:00:00Z','2026-09-01T04:00:00Z','expired',
    '20% off rose wines.','2026-05-20T15:00:00Z');

INSERT INTO promotion_tiers (promotion_id, min_bottle_equivalents, percent_off_bps) VALUES (1,6,1000),(1,12,1500);

INSERT INTO promotion_targets (promotion_target_id, promotion_id, is_exclusion, category_id, brand_id, product_id, variant_id) VALUES
 (1,1,0,1,NULL,NULL,NULL),
 (2,1,1,17,NULL,NULL,NULL),
 (3,1,1,NULL,NULL,NULL,16),
 (4,3,0,1,NULL,NULL,NULL),
 (5,3,1,17,NULL,NULL,NULL),
 (6,6,0,4,NULL,NULL,NULL);

-- -----------------------------------------------------------------------------
-- 8. Inventory balances (deterministic spread, then targeted scenarios).
--    qty_reserved and the movement ledger are derived at the end of the file.
-- -----------------------------------------------------------------------------
INSERT INTO inventory_levels (warehouse_id, variant_id, qty_on_hand, safety_stock, reorder_point, bin_location, last_counted_at, updated_at)
SELECT w.warehouse_id, l.variant_id,
       ((l.variant_id * 7 + w.warehouse_id * 13) % 40) + 8,
       CASE w.warehouse_type WHEN 'store_floor' THEN 2 ELSE 0 END,
       6,
       CASE w.warehouse_type WHEN 'store_floor' THEN 'FL-' ELSE 'FC-' END || printf('%02d', l.variant_id),
       '2026-11-01T12:00:00Z', '2026-11-18T12:00:00Z'
FROM product_listings l
JOIN warehouses w ON w.store_id = l.store_id AND w.warehouse_type <> 'temperature_controlled_cellar'
WHERE l.is_sellable = 1
  AND l.listing_status IN ('active','temporarily_unavailable','in_store_only')
  AND NOT (l.listing_status = 'in_store_only' AND w.warehouse_type = 'fulfillment_center')
  AND NOT (l.store_id = 1 AND l.variant_id IN (3, 10));

-- Collectibles live in the NJ cellar only.
INSERT INTO inventory_levels (warehouse_id, variant_id, qty_on_hand, safety_stock, reorder_point, bin_location, last_counted_at, updated_at) VALUES
 (5, 3, 4,0,0,'CEL-03','2026-11-01T12:00:00Z','2026-11-18T12:00:00Z'),
 (5,10, 9,0,0,'CEL-10','2026-11-01T12:00:00Z','2026-11-18T12:00:00Z');

UPDATE inventory_levels SET qty_on_hand = 0 WHERE warehouse_id IN (3,4) AND variant_id IN (29, 13);  -- NY out of stock / backorder
UPDATE inventory_levels SET qty_on_hand = 0 WHERE warehouse_id = 1 AND variant_id = 8;               -- NJ magnum low stock
UPDATE inventory_levels SET qty_on_hand = 3 WHERE warehouse_id = 2 AND variant_id = 8;
UPDATE inventory_levels SET qty_on_hand = 3 WHERE warehouse_id = 1 AND variant_id = 6;               -- NJ half-bottle low stock
UPDATE inventory_levels SET qty_on_hand = 0 WHERE warehouse_id = 2 AND variant_id = 6;
UPDATE inventory_levels SET qty_on_hand = 18 WHERE warehouse_id = 2 AND variant_id = 16;             -- NJ allocation
UPDATE inventory_levels SET qty_on_hand = 0 WHERE warehouse_id = 1 AND variant_id = 16;

INSERT INTO back_in_stock_subscriptions (subscription_id, customer_id, store_id, variant_id, channel, is_waitlist, status, created_at, notified_at) VALUES
 (1, 2,2,29,'email',0,'active','2026-11-12T16:10:00Z',NULL),
 (2, 1,1,15,'sms',  0,'active','2026-11-10T22:00:00Z',NULL),
 (3,10,2,13,'email',0,'active','2026-11-02T22:50:00Z',NULL),
 (4, 6,2,10,'email',1,'active','2026-09-20T14:00:00Z',NULL),
 (5, 3,1,24,'email',0,'notified','2026-08-01T12:00:00Z','2026-08-20T13:00:00Z');

-- -----------------------------------------------------------------------------
-- 9. Orders: 20 support scenarios (see README "Seed scenarios")
--    Totals start at 0 and are derived from the lines further down.
-- -----------------------------------------------------------------------------
WITH v(order_id, order_number, customer_id, store_id, channel, status, hold_reason, payment_status, fulfillment_type,
    pickup_warehouse_id, alternate_pickup_name, delivery_zone, delivery_window_start, delivery_window_end,
    substitution_preference, is_gift, gift_message, customer_note, shipping_fee_cents, tip_cents,
    tax_rate_ppm, tax_jurisdiction, placed_at, cancelled_at, cancel_reason, completed_at, created_at, updated_at) AS (VALUES
 (1, 'WA-100101', 1,1,'web',       'completed',            NULL,          'paid',              'local_delivery',NULL,NULL,1,'2026-09-12T22:00:00Z','2026-09-13T00:00:00Z','contact_me',0,NULL,'Dinner party tonight', 0,500,66250,'New Jersey (statewide)','2026-09-12T16:05:00Z',NULL,NULL,'2026-09-15T04:00:00Z','2026-09-12T16:05:00Z','2026-09-12T16:05:00Z'),
 (2, 'WA-100102', 2,2,'mobile_app','completed',            NULL,          'partially_refunded','local_delivery',NULL,NULL,1,'2026-10-03T20:00:00Z','2026-10-03T22:00:00Z','contact_me',0,NULL,NULL,                   0,400,88750,'New York City','2026-10-03T14:30:00Z',NULL,NULL,'2026-10-06T04:00:00Z','2026-10-03T14:30:00Z','2026-10-03T14:30:00Z'),
 (3, 'WA-100103', 3,1,'web',       'partially_fulfilled',  NULL,          'paid',              'shipping',      NULL,NULL,NULL,NULL,NULL,'contact_me',0,NULL,NULL,                                 0,  0,66250,'New Jersey (statewide)','2026-11-02T15:10:00Z',NULL,NULL,NULL,'2026-11-02T15:10:00Z','2026-11-02T15:10:00Z'),
 (4, 'WA-100104', 4,2,'web',       'completed',            NULL,          'partially_refunded','local_delivery',NULL,NULL,2,'2026-11-08T21:00:00Z','2026-11-08T23:00:00Z','do_not_substitute',0,NULL,'Kosher only, please', 999,0,88750,'New York City','2026-11-08T14:00:00Z',NULL,NULL,'2026-11-11T05:00:00Z','2026-11-08T14:00:00Z','2026-11-08T14:00:00Z'),
 (5, 'WA-100105', 5,1,'mobile_app','ready_for_pickup',     NULL,          'paid',              'pickup',        1,'Yusuf Rahman',NULL,NULL,NULL,'contact_me',0,NULL,NULL,                             0,  0,66250,'New Jersey (statewide)','2026-11-18T19:30:00Z',NULL,NULL,NULL,'2026-11-18T19:30:00Z','2026-11-18T19:30:00Z'),
 (6, 'WA-100106', 6,2,'web',       'completed',            NULL,          'partially_refunded','shipping',      NULL,NULL,NULL,NULL,NULL,'do_not_substitute',0,NULL,NULL,                          0,  0,83750,'Westchester County (outside cities)','2026-10-24T15:00:00Z',NULL,NULL,'2026-11-05T05:00:00Z','2026-10-24T15:00:00Z','2026-10-24T15:00:00Z'),
 (7, 'WA-100107', 7,1,'web',       'delivery_exception',   NULL,          'paid',              'shipping',      NULL,NULL,NULL,NULL,NULL,'contact_me',1,'Happy birthday, Lucia! Love, Sofia',NULL,1499,0,66250,'New Jersey (statewide)','2026-11-16T18:00:00Z',NULL,NULL,NULL,'2026-11-16T18:00:00Z','2026-11-16T18:00:00Z'),
 (8, 'WA-100108', 8,2,'web',       'on_hold',              'fraud_review','authorized',        'shipping',      NULL,NULL,NULL,NULL,NULL,'substitute_similar',0,NULL,NULL,                        0,  0,86250,'Nassau County','2026-11-17T03:30:00Z',NULL,NULL,NULL,'2026-11-17T03:30:00Z','2026-11-17T03:30:00Z'),
 (9, 'WA-100109', 9,1,'web',       'age_verification_pending',NULL,       'authorized',        'local_delivery',NULL,NULL,1,'2026-11-19T23:00:00Z','2026-11-20T01:00:00Z','contact_me',0,NULL,NULL,      599,  0,66250,'New Jersey (statewide)','2026-11-19T14:25:00Z',NULL,NULL,NULL,'2026-11-19T14:25:00Z','2026-11-19T14:25:00Z'),
 (10,'WA-100110',10,2,'web',       'cancelled',            NULL,          'partially_refunded','local_delivery',NULL,NULL,2,'2026-10-21T20:00:00Z','2026-10-21T22:00:00Z','contact_me',0,NULL,NULL,      999,  0,88750,'New York City','2026-10-20T15:00:00Z','2026-10-31T16:00:00Z','failed_delivery',NULL,'2026-10-20T15:00:00Z','2026-10-20T15:00:00Z'),
 (11,'WA-100111', 1,1,'chat_agent','completed',            NULL,          'partially_refunded','local_delivery',NULL,NULL,1,'2026-10-25T20:00:00Z','2026-10-25T22:00:00Z','contact_me',0,NULL,NULL,        0,300,66250,'New Jersey (statewide)','2026-10-25T15:00:00Z',NULL,NULL,'2026-10-28T04:00:00Z','2026-10-25T15:00:00Z','2026-10-25T15:00:00Z'),
 (12,'WA-100112',12,2,'web',       'completed',            NULL,          'partially_refunded','pickup',        3,NULL,NULL,NULL,NULL,'contact_me',0,NULL,NULL,                                    0,  0,88750,'New York City','2026-11-10T16:00:00Z',NULL,NULL,'2026-11-13T05:00:00Z','2026-11-10T16:00:00Z','2026-11-10T16:00:00Z'),
 (13,'WA-100113', 2,2,'web',       'cancelled',            NULL,          'voided',            'local_delivery',NULL,NULL,1,'2026-11-13T22:00:00Z','2026-11-14T00:00:00Z','contact_me',0,NULL,NULL,      599,  0,88750,'New York City','2026-11-12T15:30:00Z','2026-11-12T16:00:00Z','customer_request',NULL,'2026-11-12T15:30:00Z','2026-11-12T15:30:00Z'),
 (14,'WA-100114', 5,1,'web',       'completed',            NULL,          'paid',              'local_delivery',NULL,NULL,1,'2026-11-14T20:00:00Z','2026-11-14T22:00:00Z','contact_me',0,NULL,NULL,        0,300,66250,'New Jersey (statewide)','2026-11-14T15:00:00Z',NULL,NULL,'2026-11-17T05:00:00Z','2026-11-14T15:00:00Z','2026-11-14T15:00:00Z'),
 (15,'WA-100115', 6,2,'phone',     'confirmed',            NULL,          'paid',              'shipping',      NULL,NULL,NULL,NULL,NULL,'do_not_substitute',0,NULL,'Pre-arrival: ship on arrival',0,0,83750,'Westchester County (outside cities)','2026-10-05T14:00:00Z',NULL,NULL,NULL,'2026-10-05T14:00:00Z','2026-10-05T14:00:00Z'),
 (16,'WA-100116', 3,1,'web',       'delivered',            NULL,          'paid',              'shipping',      NULL,NULL,NULL,NULL,NULL,'do_not_substitute',0,NULL,NULL,                     1499,  0,66250,'New Jersey (statewide)','2026-11-09T16:00:00Z',NULL,NULL,NULL,'2026-11-09T16:00:00Z','2026-11-09T16:00:00Z'),
 (17,'WA-100117', 7,1,'mobile_app','completed',            NULL,          'paid',              'pickup',        1,NULL,NULL,NULL,NULL,'contact_me',0,NULL,NULL,                                    0,  0,66250,'New Jersey (statewide)','2026-10-18T17:00:00Z',NULL,NULL,'2026-10-19T22:00:00Z','2026-10-18T17:00:00Z','2026-10-18T17:00:00Z'),
 (18,'WA-100118',10,2,'web',       'completed',            NULL,          'paid',              'local_delivery',NULL,NULL,2,'2026-09-20T20:00:00Z','2026-09-20T22:00:00Z','contact_me',0,NULL,NULL,      999,  0,88750,'New York City','2026-09-19T20:00:00Z',NULL,NULL,'2026-09-22T04:00:00Z','2026-09-19T20:00:00Z','2026-09-19T20:00:00Z'),
 (19,'WA-100119',11,1,'web',       'on_hold',              'weather',     'authorized',        'shipping',      NULL,NULL,NULL,NULL,NULL,'contact_me',0,NULL,NULL,                           1499,  0,66250,'New Jersey (statewide)','2026-11-17T14:00:00Z',NULL,NULL,NULL,'2026-11-17T14:00:00Z','2026-11-17T14:00:00Z'),
 (20,'WA-100120', 4,2,'web',       'out_for_delivery',     NULL,          'paid',              'local_delivery',NULL,NULL,2,'2026-11-19T21:00:00Z','2026-11-19T23:00:00Z','do_not_substitute',0,NULL,NULL,   0,  0,88750,'New York City','2026-11-18T23:00:00Z',NULL,NULL,NULL,'2026-11-18T23:00:00Z','2026-11-18T23:00:00Z'))
INSERT INTO orders (order_id, order_number, customer_id, store_id, channel, status, hold_reason, payment_status, fulfillment_type,
    pickup_warehouse_id, alternate_pickup_name, delivery_zone, delivery_window_start, delivery_window_end,
    substitution_preference, is_gift, gift_message, customer_note, shipping_fee_cents, tip_cents,
    tax_rate_ppm, tax_jurisdiction, placed_at, cancelled_at, cancel_reason, completed_at, created_at, updated_at, grand_total_cents)
SELECT order_id, order_number, customer_id, store_id, channel, status, hold_reason, payment_status, fulfillment_type,
    pickup_warehouse_id, alternate_pickup_name, delivery_zone, delivery_window_start, delivery_window_end,
    substitution_preference, is_gift, gift_message, customer_note, shipping_fee_cents, tip_cents,
    tax_rate_ppm, tax_jurisdiction, placed_at, cancelled_at, cancel_reason, completed_at, created_at, updated_at, shipping_fee_cents + tip_cents FROM v;

-- Address snapshots: shipping (non-pickup orders) and billing (default billing address).
WITH m(order_id, address_id) AS (VALUES
 (1,1),(2,3),(3,4),(4,6),(6,8),(7,11),(8,13),(9,14),(10,15),(11,1),(13,3),(14,7),(15,8),(16,4),(18,15),(19,16),(20,6))
INSERT INTO order_addresses (order_id, address_role, source_address_id, recipient_name, line1, line2, city, state_code, postal_code,
                             phone_e164, address_type, delivery_instructions)
SELECT m.order_id, 'shipping', a.address_id, a.recipient_name, a.line1, a.line2, a.city, a.state_code, a.postal_code,
       a.phone_e164, a.address_type, a.delivery_instructions
FROM m JOIN customer_addresses a ON a.address_id = m.address_id;

INSERT INTO order_addresses (order_id, address_role, source_address_id, recipient_name, line1, line2, city, state_code, postal_code, phone_e164, address_type)
SELECT o.order_id, 'billing', a.address_id, a.recipient_name, a.line1, a.line2, a.city, a.state_code, a.postal_code, a.phone_e164, a.address_type
FROM orders o JOIN customer_addresses a ON a.customer_id = o.customer_id AND a.is_default_billing = 1 AND a.deleted_at IS NULL;

-- Order lines: (id, order, line, variant, price row used, qty, regular unit, charged unit, allocated discount)
WITH l(order_item_id, order_id, line_number, variant_id, price_id, quantity, unit_regular, unit_price, discount) AS (VALUES
 (1, 1,1, 4,1004,2, 3200, 3200, 640),(2, 1,2,14,1014,2, 2400, 2400, 480),(3, 1,3,28,1028,2, 1500, 1500, 300),
 (4, 2,1, 7,2007,1, 6100, 6100,   0),(5, 2,2,19,2019,1, 6800, 6800,   0),
 (6, 3,1,24,1024,3, 4200, 4200,1890),(7, 3,2,22,1022,3, 2800, 2800,1260),(8, 3,3,25,1025,3, 1900, 1900, 855),(9, 3,4,30,1030,3, 2300, 2300,1035),
 (10,4,1,32,2032,3, 2700, 2700,   0),
 (11,5,1,33,1033,2, 1800, 1800,   0),(12,5,2,34,1034,2, 1400, 1400,   0),(13,5,3,35,1035,2, 1700, 1700,   0),
 (14,6,1,16,2016,2, 7600, 7600,   0),(15,6,2, 1,2001,2, 9900, 9900,   0),(16,6,3,37,2037,1, 7200, 7200,   0),
 (17,7,1, 7,5003,1, 5800, 5299,   0),(18,7,2,31,1031,1, 6500, 6500,   0),
 (19,8,1,27,2027,6, 2900, 2900,1740),(20,8,2,36,2036,6, 4500, 4500,   0),
 (21,9,1,17,1017,4, 1600, 1600, 744),(22,9,2,18,1018,1, 2200, 2200, 256),
 (23,10,1,28,2028,3,1600, 1600,   0),(24,10,2,25,2025,1,2000, 2000,   0),
 (25,11,1,11,1011,2,2900, 2900,   0),(26,11,2,20,1020,3,4800, 4800,   0),
 (27,12,1,27,2027,2,2900, 2900,   0),
 (28,13,1,23,2023,2,3700, 3700,   0),
 (29,14,1,12,1012,2,2200, 2200,   0),(30,14,2, 5,1005,2,3400, 3400,   0),
 (31,15,1,10,2010,3,14800,14800,  0),
 (32,16,1, 1,1001,2,9500, 9500,   0),
 (33,17,1,26,1026,2,2100, 2100, 500),(34,17,2,29,1029,3,1400, 1400, 500),
 (35,18,1,36,2036,1,4500, 4500,   0),(36,18,2,38,2038,1,4200, 4200,   0),
 (37,19,1, 8,1008,1,12500,12500,  0),(38,19,2, 9,1009,2,3100, 3100,   0),
 (39,20,1,32,2032,6,2700, 2700,1620))
INSERT INTO order_items (order_item_id, order_id, line_number, variant_id, price_id, sku, product_name, brand_name, vintage_year,
                         size_ml, pack_quantity, is_final_sale, is_vintage_specific, unit_regular_price_cents, unit_price_cents,
                         quantity, line_subtotal_cents, discount_cents, tax_cents, line_total_cents, created_at)
SELECT l.order_item_id, l.order_id, l.line_number, v.variant_id, l.price_id, v.sku, p.name, b.name, v.vintage_year,
       v.size_ml, v.pack_quantity, v.is_final_sale, v.is_vintage_specific, l.unit_regular, l.unit_price,
       l.quantity, l.unit_price * l.quantity, l.discount,
       ((l.unit_price * l.quantity - l.discount) * o.tax_rate_ppm + 500000) / 1000000,
       l.unit_price * l.quantity - l.discount + ((l.unit_price * l.quantity - l.discount) * o.tax_rate_ppm + 500000) / 1000000,
       o.placed_at
FROM l
JOIN orders o ON o.order_id = l.order_id
JOIN product_variants v ON v.variant_id = l.variant_id
JOIN products p ON p.product_id = v.product_id
JOIN brands b ON b.brand_id = p.brand_id;

-- Derive order totals from the lines (+ tax on delivery/shipping fees).
UPDATE orders SET
    items_subtotal_cents = agg.sub,
    discount_total_cents = agg.disc,
    tax_total_cents      = agg.tax + (orders.shipping_fee_cents * orders.tax_rate_ppm + 500000) / 1000000,
    grand_total_cents    = agg.sub - agg.disc + orders.shipping_fee_cents + orders.tip_cents
                           + agg.tax + (orders.shipping_fee_cents * orders.tax_rate_ppm + 500000) / 1000000
FROM (SELECT order_id, SUM(line_subtotal_cents) AS sub, SUM(discount_cents) AS disc, SUM(tax_cents) AS tax
      FROM order_items GROUP BY order_id) AS agg
WHERE agg.order_id = orders.order_id;

-- Discounts and their per-line allocation.
INSERT INTO order_discounts (order_discount_id, order_id, promotion_id, discount_type, code_used, description, amount_cents, created_at)
SELECT d.id, d.order_id, d.promotion_id, d.discount_type, d.code_used, d.description,
       (SELECT SUM(discount_cents) FROM order_items WHERE order_id = d.order_id),
       (SELECT placed_at FROM orders WHERE order_id = d.order_id)
FROM (SELECT 1 AS id, 1 AS order_id, 1 AS promotion_id, 'mixed_case' AS discount_type, NULL AS code_used, 'Mixed case 10% (6 bottles)' AS description
      UNION ALL SELECT 2, 3, 1, 'mixed_case', NULL, 'Mixed case 15% (12 bottles)'
      UNION ALL SELECT 3, 8, 1, 'mixed_case', NULL, 'Mixed case 10% (6 eligible wines)'
      UNION ALL SELECT 4, 9, 2, 'first_order', 'WELCOME10', 'First order $10 off'
      UNION ALL SELECT 5,17, 5, 'loyalty_reward', NULL, 'Rewards $10 reward'
      UNION ALL SELECT 6,20, 1, 'mixed_case', NULL, 'Mixed case 10% (6 bottles)') AS d;

INSERT INTO order_discount_allocations (order_discount_id, order_id, order_item_id, amount_cents)
SELECT d.order_discount_id, i.order_id, i.order_item_id, i.discount_cents
FROM order_items i JOIN order_discounts d ON d.order_id = i.order_id
WHERE i.discount_cents > 0;

-- O-13: whole order cancelled before picking; O-14: one Sancerre removed after a declined substitution.
UPDATE order_items SET quantity_cancelled = quantity WHERE order_id = 13;
UPDATE order_items SET quantity_cancelled = 1 WHERE order_item_id = 30;

INSERT INTO order_item_substitutions (substitution_id, order_id, order_item_id, proposed_variant_id, proposed_unit_price_cents,
                                      substitution_type, requires_consent, status, decided_by_type, proposed_at, expires_at, decided_at) VALUES
 (1,14,30,4,3200,'adjacent_vintage',1,'declined','customer','2026-11-14T19:20:00Z','2026-11-15T19:20:00Z','2026-11-14T19:48:00Z');

-- Status timelines (from_status is derived with LAG).
WITH h(order_id, to_status, actor_type, actor_ref, note, changed_at) AS (VALUES
 (1,'placed','customer','C-100001',NULL,'2026-09-12T16:05:00Z'),(1,'confirmed','system','order-service',NULL,'2026-09-12T16:06:00Z'),
 (1,'picking','staff','S-1004',NULL,'2026-09-12T21:00:00Z'),(1,'out_for_delivery','staff','S-1004',NULL,'2026-09-12T22:10:00Z'),
 (1,'delivered','staff','S-1004','ID checked at door','2026-09-12T23:05:00Z'),(1,'completed','system','order-service',NULL,'2026-09-15T04:00:00Z'),
 (2,'placed','customer','C-100002',NULL,'2026-10-03T14:30:00Z'),(2,'confirmed','system','order-service',NULL,'2026-10-03T14:31:00Z'),
 (2,'picking','staff','S-1005',NULL,'2026-10-03T19:00:00Z'),(2,'out_for_delivery','staff','S-1005',NULL,'2026-10-03T20:05:00Z'),
 (2,'delivered','staff','S-1005',NULL,'2026-10-03T20:50:00Z'),(2,'completed','system','order-service',NULL,'2026-10-06T04:00:00Z'),
 (3,'placed','customer','C-100003',NULL,'2026-11-02T15:10:00Z'),(3,'confirmed','system','order-service',NULL,'2026-11-02T15:11:00Z'),
 (3,'picking','staff','S-1004',NULL,'2026-11-03T14:00:00Z'),(3,'label_created','system','shipping-service',NULL,'2026-11-03T18:00:00Z'),
 (3,'in_transit','carrier','UPS',NULL,'2026-11-03T22:00:00Z'),
 (3,'partially_fulfilled','system','order-service','9 of 12 delivered; 3 Mosel Kabinett backordered, ship on receipt','2026-11-06T19:40:00Z'),
 (4,'placed','customer','C-100004',NULL,'2026-11-08T14:00:00Z'),(4,'confirmed','system','order-service',NULL,'2026-11-08T14:01:00Z'),
 (4,'picking','staff','S-1005',NULL,'2026-11-08T20:30:00Z'),(4,'out_for_delivery','staff','S-1005',NULL,'2026-11-08T21:40:00Z'),
 (4,'delivered','staff','S-1005','Delivered 85 min after window end','2026-11-09T00:25:00Z'),(4,'completed','system','order-service',NULL,'2026-11-11T05:00:00Z'),
 (5,'placed','customer','C-100005',NULL,'2026-11-18T19:30:00Z'),(5,'confirmed','system','order-service',NULL,'2026-11-18T19:31:00Z'),
 (5,'picking','staff','S-1004',NULL,'2026-11-18T20:15:00Z'),(5,'ready_for_pickup','staff','S-1004','Shelf P-12','2026-11-18T21:00:00Z'),
 (6,'placed','customer','C-100006',NULL,'2026-10-24T15:00:00Z'),(6,'confirmed','system','order-service',NULL,'2026-10-24T15:01:00Z'),
 (6,'picking','staff','S-1005',NULL,'2026-10-26T14:00:00Z'),(6,'label_created','system','shipping-service',NULL,'2026-10-26T17:00:00Z'),
 (6,'in_transit','carrier','UPS',NULL,'2026-10-26T22:00:00Z'),(6,'delivered','carrier','UPS','Adult signature','2026-10-28T18:30:00Z'),
 (6,'completed','system','order-service',NULL,'2026-11-05T05:00:00Z'),
 (7,'placed','customer','C-100007',NULL,'2026-11-16T18:00:00Z'),(7,'confirmed','system','order-service',NULL,'2026-11-16T18:01:00Z'),
 (7,'picking','staff','S-1004',NULL,'2026-11-17T14:00:00Z'),(7,'label_created','system','shipping-service',NULL,'2026-11-17T16:00:00Z'),
 (7,'in_transit','carrier','UPS',NULL,'2026-11-17T22:00:00Z'),(7,'delivery_exception','carrier','UPS','No adult available to sign (attempt 1 of 3)','2026-11-18T20:15:00Z'),
 (8,'placed','customer','C-100008','Placed from new device','2026-11-17T03:30:00Z'),
 (8,'on_hold','system','fraud-rules','Fraud review: new device, new address, high-value spirits','2026-11-17T03:31:00Z'),
 (9,'placed','customer','C-100009',NULL,'2026-11-19T14:25:00Z'),(9,'age_verification_pending','system','order-service','First order: ID check required (A-05)','2026-11-19T14:25:30Z'),
 (10,'placed','customer','C-100010',NULL,'2026-10-20T15:00:00Z'),(10,'confirmed','system','order-service',NULL,'2026-10-20T15:01:00Z'),
 (10,'picking','staff','S-1005',NULL,'2026-10-21T19:00:00Z'),(10,'out_for_delivery','staff','S-1005',NULL,'2026-10-21T20:00:00Z'),
 (10,'delivery_failed','staff','S-1005','No answer; no adult available','2026-10-21T21:30:00Z'),
 (10,'redelivery_scheduled','ai_agent','wines-ai-agent','Free redelivery booked (A-17)','2026-10-22T14:00:00Z'),
 (10,'out_for_delivery','staff','S-1005',NULL,'2026-10-23T20:00:00Z'),(10,'delivery_failed','staff','S-1005','Second failed attempt','2026-10-23T21:20:00Z'),
 (10,'returned_to_store','staff','S-1005','Held for pickup 7 days (A-17)','2026-10-23T22:30:00Z'),
 (10,'cancelled','system','order-service','Pickup hold expired; refund minus delivery fee','2026-10-31T16:00:00Z'),
 (11,'placed','ai_agent','wines-ai-agent','Order placed in chat with customer confirmation','2026-10-25T15:00:00Z'),(11,'confirmed','system','order-service',NULL,'2026-10-25T15:01:00Z'),
 (11,'picking','staff','S-1004',NULL,'2026-10-25T19:00:00Z'),(11,'out_for_delivery','staff','S-1004',NULL,'2026-10-25T20:00:00Z'),
 (11,'delivered','staff','S-1004',NULL,'2026-10-25T20:40:00Z'),(11,'completed','system','order-service',NULL,'2026-10-28T04:00:00Z'),
 (12,'placed','customer','C-100012',NULL,'2026-11-10T16:00:00Z'),(12,'confirmed','system','order-service',NULL,'2026-11-10T16:01:00Z'),
 (12,'picking','staff','S-1005',NULL,'2026-11-10T17:00:00Z'),(12,'ready_for_pickup','staff','S-1005',NULL,'2026-11-10T17:45:00Z'),
 (12,'picked_up','staff','S-1005','ID checked at counter','2026-11-11T22:10:00Z'),(12,'completed','system','order-service',NULL,'2026-11-13T05:00:00Z'),
 (13,'placed','customer','C-100002',NULL,'2026-11-12T15:30:00Z'),
 (13,'cancelled','ai_agent','wines-ai-agent','Customer asked to cancel before picking (A-21)','2026-11-12T16:00:00Z'),
 (14,'placed','customer','C-100005',NULL,'2026-11-14T15:00:00Z'),(14,'confirmed','system','order-service',NULL,'2026-11-14T15:01:00Z'),
 (14,'picking','staff','S-1004',NULL,'2026-11-14T19:00:00Z'),(14,'substitution_pending','staff','S-1004','Only 1 of 2 Sancerre 2024 on hand','2026-11-14T19:20:00Z'),
 (14,'picking','customer','C-100005','Substitution declined; 1 unit removed','2026-11-14T19:50:00Z'),
 (14,'out_for_delivery','staff','S-1004',NULL,'2026-11-14T20:30:00Z'),(14,'delivered','staff','S-1004',NULL,'2026-11-14T21:10:00Z'),
 (14,'completed','system','order-service',NULL,'2026-11-17T05:00:00Z'),
 (15,'placed','staff','S-1002','Phone order, pre-arrival paid in full (A-25)','2026-10-05T14:00:00Z'),(15,'confirmed','system','order-service',NULL,'2026-10-05T14:01:00Z'),
 (16,'placed','customer','C-100003',NULL,'2026-11-09T16:00:00Z'),(16,'confirmed','system','order-service',NULL,'2026-11-09T16:01:00Z'),
 (16,'picking','staff','S-1004',NULL,'2026-11-10T14:00:00Z'),(16,'label_created','system','shipping-service',NULL,'2026-11-10T16:00:00Z'),
 (16,'in_transit','carrier','UPS',NULL,'2026-11-10T22:00:00Z'),(16,'delivered','carrier','UPS','Adult signature','2026-11-13T18:00:00Z'),
 (17,'placed','customer','C-100007',NULL,'2026-10-18T17:00:00Z'),(17,'confirmed','system','order-service',NULL,'2026-10-18T17:01:00Z'),
 (17,'picking','staff','S-1004',NULL,'2026-10-18T17:30:00Z'),(17,'ready_for_pickup','staff','S-1004',NULL,'2026-10-18T18:30:00Z'),
 (17,'picked_up','staff','S-1004','ID checked at counter','2026-10-19T21:30:00Z'),(17,'completed','system','order-service',NULL,'2026-10-19T22:00:00Z'),
 (18,'placed','customer','C-100010',NULL,'2026-09-19T20:00:00Z'),(18,'confirmed','system','order-service',NULL,'2026-09-19T20:01:00Z'),
 (18,'picking','staff','S-1005',NULL,'2026-09-20T19:00:00Z'),(18,'out_for_delivery','staff','S-1005',NULL,'2026-09-20T20:00:00Z'),
 (18,'delivered','staff','S-1005',NULL,'2026-09-20T20:45:00Z'),(18,'completed','system','order-service',NULL,'2026-09-22T04:00:00Z'),
 (19,'placed','customer','C-100011',NULL,'2026-11-17T14:00:00Z'),(19,'confirmed','system','order-service',NULL,'2026-11-17T14:01:00Z'),
 (19,'picking','staff','S-1004',NULL,'2026-11-18T14:00:00Z'),
 (19,'on_hold','system','shipping-service','Weather hold: destination forecast below 28F (A-19)','2026-11-18T15:00:00Z'),
 (20,'placed','customer','C-100004',NULL,'2026-11-18T23:00:00Z'),(20,'confirmed','system','order-service',NULL,'2026-11-18T23:01:00Z'),
 (20,'picking','staff','S-1005',NULL,'2026-11-19T19:00:00Z'),(20,'out_for_delivery','staff','S-1005',NULL,'2026-11-19T20:40:00Z'))
INSERT INTO order_status_history (order_id, from_status, to_status, actor_type, actor_ref, note, changed_at)
SELECT order_id, LAG(to_status) OVER (PARTITION BY order_id ORDER BY changed_at), to_status, actor_type, actor_ref, note, changed_at
FROM h ORDER BY order_id, changed_at;

UPDATE orders SET updated_at = (SELECT MAX(changed_at) FROM order_status_history h WHERE h.order_id = orders.order_id);

-- -----------------------------------------------------------------------------
-- 10. Gift cards and payments (split tenders: O-6 gift card + card, O-20 store credit + card)
-- -----------------------------------------------------------------------------
INSERT INTO gift_cards (gift_card_id, code_hash, code_last4, card_format, initial_value_cents, status, purchaser_customer_id,
                        purchase_order_id, recipient_email, issued_at) VALUES
 (1,'sha256:demo-giftcard-0001','7314','digital', 15000,'active',1,NULL,'robert.fitzgerald@example.org','2026-09-01T15:00:00Z'),
 (2,'sha256:demo-giftcard-0002','0558','digital',  5000,'active',2,NULL,'james.okafor@example.net','2026-10-10T15:00:00Z'),
 (3,'sha256:demo-giftcard-0003','9921','physical',20000,'frozen',8,NULL,NULL,'2026-11-17T03:40:00Z');

-- (payment_id, order_id, tender, saved method, gift card, amount: NULL = rest of order, status, refund_priority)
WITH t(payment_id, order_id, tender_type, payment_method_id, gift_card_id, fixed_amount, status, refund_priority) AS (VALUES
 (1, 1,'card',1,NULL,NULL,'captured',1),            (2, 2,'card',3,NULL,NULL,'partially_refunded',1),
 (3, 3,'card',4,NULL,NULL,'captured',1),            (4, 4,'card',5,NULL,NULL,'partially_refunded',1),
 (5, 5,'google_pay',6,NULL,NULL,'captured',1),      (6, 6,'card',7,NULL,NULL,'captured',2),
 (7, 7,'apple_pay',8,NULL,NULL,'captured',1),       (8, 8,'card',9,NULL,NULL,'authorized',1),
 (9, 9,'card',10,NULL,NULL,'authorized',1),         (10,10,'card',11,NULL,NULL,'partially_refunded',1),
 (11,11,'apple_pay',2,NULL,NULL,'partially_refunded',1),(12,12,'card',13,NULL,NULL,'partially_refunded',1),
 (13,13,'card',3,NULL,NULL,'voided',1),             (14,14,'google_pay',6,NULL,NULL,'captured',1),
 (15,15,'card',7,NULL,NULL,'captured',1),           (16,16,'card',4,NULL,NULL,'captured',1),
 (17,17,'apple_pay',8,NULL,NULL,'captured',1),      (18,18,'card',11,NULL,NULL,'captured',1),
 (19,19,'card',12,NULL,NULL,'authorized',1),        (20,20,'card',5,NULL,NULL,'captured',2),
 (21, 6,'gift_card',NULL,1,10000,'captured',1),     (22,20,'store_credit',NULL,NULL,1000,'captured',1))
INSERT INTO payments (payment_id, order_id, customer_id, tender_type, payment_method_id, gift_card_id, processor, processor_payment_ref,
                      amount_cents, status, refund_priority, created_at, updated_at)
SELECT t.payment_id, t.order_id, o.customer_id, t.tender_type, t.payment_method_id, t.gift_card_id,
       CASE WHEN t.tender_type IN ('gift_card','store_credit') THEN 'internal_ledger' ELSE 'card_gateway' END,
       CASE WHEN t.tender_type IN ('gift_card','store_credit') THEN NULL ELSE 'pi_demo_' || printf('%06d', t.payment_id) END,
       COALESCE(t.fixed_amount,
                o.grand_total_cents - COALESCE((SELECT SUM(fixed_amount) FROM t t2 WHERE t2.order_id = t.order_id AND t2.fixed_amount IS NOT NULL), 0)),
       t.status, t.refund_priority, o.placed_at, o.updated_at
FROM t JOIN orders o ON o.order_id = t.order_id;

-- Authorization for every tender at placement. Transaction id scheme:
-- payment_id*10 + 1 auth, +2/+3 captures, +5 void, +6/+7 refunds, +8 chargeback.
INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents,
                                  processor_reference, idempotency_key, created_at, processed_at)
SELECT p.payment_id * 10 + 1, p.payment_id, p.order_id, 'authorization', 'succeeded', p.amount_cents,
       'auth_demo_' || (p.payment_id * 10 + 1), 'seed-ptx-' || (p.payment_id * 10 + 1),
       strftime('%Y-%m-%dT%H:%M:%SZ', o.placed_at, '+20 seconds'), strftime('%Y-%m-%dT%H:%M:%SZ', o.placed_at, '+22 seconds')
FROM payments p JOIN orders o ON o.order_id = p.order_id;

-- -----------------------------------------------------------------------------
-- 11. Shipments, lines and tracking (O-3 is split into two shipments)
-- -----------------------------------------------------------------------------
INSERT INTO shipments (shipment_id, shipment_number, order_id, store_id, warehouse_id, method, carrier, service_level, tracking_number, tracking_url,
                       status, requires_adult_signature, weather_hold, attempt_count, delivery_window_start, delivery_window_end, estimated_delivery_at,
                       shipping_cost_cents, shipped_at, delivered_at, handed_to_name, id_check_method, id_verified, created_at, updated_at) VALUES
 (1, 'SH-200001', 1,1,1,'local_delivery','store_driver',NULL,NULL,NULL,'delivered',1,0,1,'2026-09-12T22:00:00Z','2026-09-13T00:00:00Z',NULL,450,'2026-09-12T22:10:00Z','2026-09-12T23:05:00Z','Olivia Martinez','id_scan',1,'2026-09-12T21:00:00Z','2026-09-12T23:05:00Z'),
 (2, 'SH-200002', 2,2,3,'local_delivery','store_driver',NULL,NULL,NULL,'delivered',1,0,1,'2026-10-03T20:00:00Z','2026-10-03T22:00:00Z',NULL,520,'2026-10-03T20:05:00Z','2026-10-03T20:50:00Z','James Okafor','id_scan',1,'2026-10-03T19:00:00Z','2026-10-03T20:50:00Z'),
 (3, 'SH-200003', 3,1,2,'carrier','UPS','Ground - Adult Signature Required','1ZDEMO0000000003','https://tracking.example.com/1ZDEMO0000000003','delivered',1,0,1,NULL,NULL,'2026-11-06T23:00:00Z',1840,'2026-11-03T22:00:00Z','2026-11-06T19:30:00Z','Mei Chen','carrier_adult_signature',1,'2026-11-03T18:00:00Z','2026-11-06T19:30:00Z'),
 (4, 'SH-200004', 3,1,2,'carrier','UPS','Ground - Adult Signature Required','1ZDEMO0000000004','https://tracking.example.com/1ZDEMO0000000004','in_transit',1,0,0,NULL,NULL,'2026-11-20T23:00:00Z',1210,'2026-11-17T22:00:00Z',NULL,NULL,NULL,0,'2026-11-17T18:00:00Z','2026-11-19T06:00:00Z'),
 (5, 'SH-200005', 4,2,3,'local_delivery','store_driver',NULL,NULL,NULL,'delivered',1,0,1,'2026-11-08T21:00:00Z','2026-11-08T23:00:00Z',NULL,610,'2026-11-08T21:40:00Z','2026-11-09T00:25:00Z','Daniel Rosenberg','id_scan',1,'2026-11-08T20:30:00Z','2026-11-09T00:25:00Z'),
 (6, 'SH-200006', 5,1,1,'pickup',NULL,NULL,NULL,NULL,'ready_for_pickup',1,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,'2026-11-18T20:15:00Z','2026-11-18T21:00:00Z'),
 (7, 'SH-200007', 6,2,4,'carrier','UPS','Ground - Adult Signature Required','1ZDEMO0000000007','https://tracking.example.com/1ZDEMO0000000007','delivered',1,0,1,NULL,NULL,'2026-10-28T23:00:00Z',1650,'2026-10-26T22:00:00Z','2026-10-28T18:30:00Z','Robert Fitzgerald','carrier_adult_signature',1,'2026-10-26T17:00:00Z','2026-10-28T18:30:00Z'),
 (8, 'SH-200008', 7,1,2,'carrier','UPS','Ground - Adult Signature Required','1ZDEMO0000000008','https://tracking.example.com/1ZDEMO0000000008','delivery_exception',1,0,1,NULL,NULL,'2026-11-19T23:00:00Z',1320,'2026-11-17T22:00:00Z',NULL,NULL,NULL,0,'2026-11-17T16:00:00Z','2026-11-18T20:15:00Z'),
 (9, 'SH-200009',10,2,3,'local_delivery','store_driver',NULL,NULL,NULL,'returned_to_store',1,0,2,'2026-10-23T20:00:00Z','2026-10-23T22:00:00Z',NULL,1040,'2026-10-21T20:00:00Z',NULL,NULL,NULL,0,'2026-10-21T19:00:00Z','2026-10-23T22:30:00Z'),
 (10,'SH-200010',11,1,1,'local_delivery','store_driver',NULL,NULL,NULL,'delivered',1,0,1,'2026-10-25T20:00:00Z','2026-10-25T22:00:00Z',NULL,450,'2026-10-25T20:00:00Z','2026-10-25T20:40:00Z','Olivia Martinez','id_scan',1,'2026-10-25T19:00:00Z','2026-10-25T20:40:00Z'),
 (11,'SH-200011',12,2,3,'pickup',NULL,NULL,NULL,NULL,'picked_up',1,0,0,NULL,NULL,NULL,NULL,'2026-11-11T22:10:00Z','2026-11-11T22:10:00Z','Michael Brennan','id_scan',1,'2026-11-10T17:00:00Z','2026-11-11T22:10:00Z'),
 (12,'SH-200012',14,1,1,'local_delivery','store_driver',NULL,NULL,NULL,'delivered',1,0,1,'2026-11-14T20:00:00Z','2026-11-14T22:00:00Z',NULL,450,'2026-11-14T20:30:00Z','2026-11-14T21:10:00Z','Aisha Rahman','id_scan',1,'2026-11-14T19:00:00Z','2026-11-14T21:10:00Z'),
 (13,'SH-200013',16,1,2,'carrier','UPS','Ground - Adult Signature Required','1ZDEMO0000000013','https://tracking.example.com/1ZDEMO0000000013','delivered',1,0,1,NULL,NULL,'2026-11-13T23:00:00Z',1180,'2026-11-10T22:00:00Z','2026-11-13T18:00:00Z','Mei Chen','carrier_adult_signature',1,'2026-11-10T16:00:00Z','2026-11-13T18:00:00Z'),
 (14,'SH-200014',17,1,1,'pickup',NULL,NULL,NULL,NULL,'picked_up',1,0,0,NULL,NULL,NULL,NULL,'2026-10-19T21:30:00Z','2026-10-19T21:30:00Z','Sofia Bianchi','id_scan',1,'2026-10-18T17:30:00Z','2026-10-19T21:30:00Z'),
 (15,'SH-200015',18,2,3,'local_delivery','courier_partner',NULL,NULL,NULL,'delivered',1,0,1,'2026-09-20T20:00:00Z','2026-09-20T22:00:00Z',NULL,890,'2026-09-20T20:00:00Z','2026-09-20T20:45:00Z','Carlos Mendes','visual_id_check',1,'2026-09-20T19:00:00Z','2026-09-20T20:45:00Z'),
 (16,'SH-200016',19,1,2,'carrier','UPS','Ground - Adult Signature Required',NULL,NULL,'packed',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,'2026-11-18T14:00:00Z','2026-11-18T15:00:00Z'),
 (17,'SH-200017',20,2,3,'local_delivery','store_driver',NULL,NULL,NULL,'out_for_delivery',1,0,1,'2026-11-19T21:00:00Z','2026-11-19T23:00:00Z',NULL,610,'2026-11-19T20:40:00Z',NULL,NULL,NULL,0,'2026-11-19T19:00:00Z','2026-11-19T20:40:00Z');

-- Single-shipment orders ship every non-cancelled unit; O-3 is split by line.
INSERT INTO shipment_items (shipment_id, order_id, order_item_id, quantity)
SELECT s.shipment_id, i.order_id, i.order_item_id, i.quantity - i.quantity_cancelled
FROM shipments s JOIN order_items i ON i.order_id = s.order_id
WHERE s.order_id <> 3 AND i.quantity > i.quantity_cancelled;
INSERT INTO shipment_items (shipment_id, order_id, order_item_id, quantity) VALUES
 (3,3,6,3),(3,3,7,3),(3,3,8,3),
 (4,3,9,3);

WITH e(shipment_id, event_code, description, location_city, location_state, source, occurred_at) AS (VALUES
 (1,'driver_assigned','Driver assigned','Hoboken','NJ','driver_app','2026-09-12T22:05:00Z'),
 (1,'out_for_delivery','Out for delivery','Hoboken','NJ','driver_app','2026-09-12T22:10:00Z'),
 (1,'delivered','Delivered; ID scanned (21+)','Hoboken','NJ','driver_app','2026-09-12T23:05:00Z'),
 (2,'out_for_delivery','Out for delivery','New York','NY','driver_app','2026-10-03T20:05:00Z'),
 (2,'delivered','Delivered; ID scanned (21+)','New York','NY','driver_app','2026-10-03T20:50:00Z'),
 (3,'label_created','Shipping label created','Secaucus','NJ','system','2026-11-03T18:00:00Z'),
 (3,'carrier_pickup','Picked up by carrier','Secaucus','NJ','carrier_webhook','2026-11-03T22:00:00Z'),
 (3,'in_transit','Departed facility','Edison','NJ','carrier_webhook','2026-11-04T08:00:00Z'),
 (3,'out_for_delivery','Out for delivery','Princeton','NJ','carrier_webhook','2026-11-06T13:00:00Z'),
 (3,'delivered','Delivered; adult signature obtained','Princeton','NJ','carrier_webhook','2026-11-06T19:30:00Z'),
 (4,'label_created','Shipping label created (backordered line)','Secaucus','NJ','system','2026-11-17T18:00:00Z'),
 (4,'carrier_pickup','Picked up by carrier','Secaucus','NJ','carrier_webhook','2026-11-17T22:00:00Z'),
 (4,'in_transit','Departed facility','Edison','NJ','carrier_webhook','2026-11-18T09:00:00Z'),
 (4,'arrived_at_facility','Arrived at local facility','Hamilton','NJ','carrier_webhook','2026-11-19T06:00:00Z'),
 (5,'out_for_delivery','Out for delivery','New York','NY','driver_app','2026-11-08T21:40:00Z'),
 (5,'delivered','Delivered after window; ID scanned (21+)','Brooklyn','NY','driver_app','2026-11-09T00:25:00Z'),
 (6,'ready_for_pickup','Ready at Hoboken counter, shelf P-12','Hoboken','NJ','store_staff','2026-11-18T21:00:00Z'),
 (7,'label_created','Shipping label created','Long Island City','NY','system','2026-10-26T17:00:00Z'),
 (7,'carrier_pickup','Picked up by carrier','Long Island City','NY','carrier_webhook','2026-10-26T22:00:00Z'),
 (7,'in_transit','Departed facility','Elmsford','NY','carrier_webhook','2026-10-27T10:00:00Z'),
 (7,'out_for_delivery','Out for delivery','Scarsdale','NY','carrier_webhook','2026-10-28T13:00:00Z'),
 (7,'delivered','Delivered; adult signature obtained','Scarsdale','NY','carrier_webhook','2026-10-28T18:30:00Z'),
 (8,'label_created','Shipping label created','Secaucus','NJ','system','2026-11-17T16:00:00Z'),
 (8,'carrier_pickup','Picked up by carrier','Secaucus','NJ','carrier_webhook','2026-11-17T22:00:00Z'),
 (8,'in_transit','Departed facility','Parsippany','NJ','carrier_webhook','2026-11-18T06:00:00Z'),
 (8,'out_for_delivery','Out for delivery','Morristown','NJ','carrier_webhook','2026-11-18T13:00:00Z'),
 (8,'delivery_attempted','Delivery attempted: no adult 21+ available to sign','Morristown','NJ','carrier_webhook','2026-11-18T20:10:00Z'),
 (8,'delivery_exception','Next attempt next business day (attempt 1 of 3)','Morristown','NJ','carrier_webhook','2026-11-18T20:15:00Z'),
 (9,'out_for_delivery','Out for delivery','New York','NY','driver_app','2026-10-21T20:00:00Z'),
 (9,'delivery_attempted','No answer; customer not reachable','Astoria','NY','driver_app','2026-10-21T21:30:00Z'),
 (9,'out_for_delivery','Redelivery out for delivery','New York','NY','driver_app','2026-10-23T20:00:00Z'),
 (9,'delivery_attempted','Second attempt failed; no adult available','Astoria','NY','driver_app','2026-10-23T21:20:00Z'),
 (9,'returned_to_store','Returned to Chelsea store; held 7 days','New York','NY','store_staff','2026-10-23T22:30:00Z'),
 (10,'out_for_delivery','Out for delivery','Hoboken','NJ','driver_app','2026-10-25T20:00:00Z'),
 (10,'delivered','Delivered; ID scanned (21+)','Hoboken','NJ','driver_app','2026-10-25T20:40:00Z'),
 (11,'ready_for_pickup','Ready at Chelsea counter','New York','NY','store_staff','2026-11-10T17:45:00Z'),
 (11,'picked_up','Picked up; ID scanned (21+)','New York','NY','store_staff','2026-11-11T22:10:00Z'),
 (12,'out_for_delivery','Out for delivery','Hoboken','NJ','driver_app','2026-11-14T20:30:00Z'),
 (12,'delivered','Delivered; ID scanned (21+)','Jersey City','NJ','driver_app','2026-11-14T21:10:00Z'),
 (13,'label_created','Shipping label created','Secaucus','NJ','system','2026-11-10T16:00:00Z'),
 (13,'carrier_pickup','Picked up by carrier','Secaucus','NJ','carrier_webhook','2026-11-10T22:00:00Z'),
 (13,'in_transit','Departed facility','Edison','NJ','carrier_webhook','2026-11-11T09:00:00Z'),
 (13,'out_for_delivery','Out for delivery','Princeton','NJ','carrier_webhook','2026-11-13T13:00:00Z'),
 (13,'delivered','Delivered; adult signature obtained','Princeton','NJ','carrier_webhook','2026-11-13T18:00:00Z'),
 (14,'ready_for_pickup','Ready at Hoboken counter','Hoboken','NJ','store_staff','2026-10-18T18:30:00Z'),
 (14,'picked_up','Picked up; ID scanned (21+)','Hoboken','NJ','store_staff','2026-10-19T21:30:00Z'),
 (15,'driver_assigned','Courier assigned','New York','NY','driver_app','2026-09-20T19:50:00Z'),
 (15,'out_for_delivery','Out for delivery','New York','NY','driver_app','2026-09-20T20:00:00Z'),
 (15,'delivered','Delivered; ID checked (21+)','Astoria','NY','driver_app','2026-09-20T20:45:00Z'),
 (16,'weather_hold','Held: destination forecast below 28F (A-19)','Secaucus','NJ','system','2026-11-18T15:00:00Z'),
 (17,'driver_assigned','Driver assigned','New York','NY','driver_app','2026-11-19T20:35:00Z'),
 (17,'out_for_delivery','Out for delivery; ETA 4:20-4:40 pm','New York','NY','driver_app','2026-11-19T20:40:00Z'))
INSERT INTO shipment_tracking_events (shipment_id, event_code, description, location_city, location_state, source, carrier_event_ref,
                                      raw_payload, occurred_at, received_at)
SELECT e.shipment_id, e.event_code, e.description, e.location_city, e.location_state, e.source,
       CASE WHEN e.source = 'carrier_webhook' THEN 'ups-evt-' || e.shipment_id || '-' || replace(replace(e.occurred_at,':',''),'-','') END,
       CASE WHEN e.source = 'carrier_webhook' THEN json_object('carrier','UPS','tracking_number', s.tracking_number, 'status', e.event_code) END,
       e.occurred_at, strftime('%Y-%m-%dT%H:%M:%SZ', e.occurred_at, '+1 minute')
FROM e JOIN shipments s ON s.shipment_id = e.shipment_id
ORDER BY e.occurred_at;

-- Captures: at dispatch for deliveries/shipments (A-29), at placement for prepaid
-- pickup and pre-arrival orders. O-3 = two partial captures; O-14 = partial capture + void.
WITH c(payment_id, shipment_id, captured_at) AS (VALUES
 (1,1,'2026-09-12T22:10:00Z'),(2,2,'2026-10-03T20:05:00Z'),(4,5,'2026-11-08T21:40:00Z'),(5,NULL,'2026-11-18T19:31:00Z'),
 (6,7,'2026-10-26T22:00:00Z'),(21,7,'2026-10-26T22:00:00Z'),(7,8,'2026-11-17T22:00:00Z'),(10,9,'2026-10-21T20:00:00Z'),
 (11,10,'2026-10-25T20:00:00Z'),(12,NULL,'2026-11-10T16:01:00Z'),(15,NULL,'2026-10-05T14:01:00Z'),(16,13,'2026-11-10T22:00:00Z'),
 (17,NULL,'2026-10-18T17:01:00Z'),(18,15,'2026-09-20T20:00:00Z'),(20,17,'2026-11-19T20:40:00Z'),(22,17,'2026-11-19T20:40:00Z'))
INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents, parent_transaction_id,
                                  shipment_id, processor_reference, idempotency_key, created_at, processed_at)
SELECT p.payment_id * 10 + 2, p.payment_id, p.order_id, 'capture', 'succeeded', p.amount_cents, p.payment_id * 10 + 1,
       c.shipment_id, 'cap_demo_' || (p.payment_id * 10 + 2), 'seed-ptx-' || (p.payment_id * 10 + 2), c.captured_at, c.captured_at
FROM c JOIN payments p ON p.payment_id = c.payment_id;

INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents, parent_transaction_id,
                                  shipment_id, processor_reference, idempotency_key, created_at, processed_at)
SELECT 32, 3, 3, 'capture', 'succeeded', SUM(line_total_cents), 31, 3, 'cap_demo_32', 'seed-ptx-32', '2026-11-03T22:00:00Z', '2026-11-03T22:00:05Z'
FROM order_items WHERE order_item_id IN (6,7,8)
UNION ALL
SELECT 33, 3, 3, 'capture', 'succeeded', line_total_cents, 31, 4, 'cap_demo_33', 'seed-ptx-33', '2026-11-17T22:00:00Z', '2026-11-17T22:00:05Z'
FROM order_items WHERE order_item_id = 9
UNION ALL
SELECT 142, 14, 14, 'capture', 'succeeded',
       o.grand_total_cents - i.line_total_cents * i.quantity_cancelled / i.quantity, 141, 12,
       'cap_demo_142', 'seed-ptx-142', '2026-11-14T20:30:00Z', '2026-11-14T20:30:05Z'
FROM orders o JOIN order_items i ON i.order_item_id = 30 WHERE o.order_id = 14;

INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents, parent_transaction_id,
                                  processor_reference, idempotency_key, created_at, processed_at)
SELECT 145, 14, 14, 'void', 'succeeded', i.line_total_cents * i.quantity_cancelled / i.quantity, 141,
       'void_demo_145', 'seed-ptx-145', '2026-11-14T20:30:10Z', '2026-11-14T20:30:12Z'
FROM order_items i WHERE i.order_item_id = 30
UNION ALL
SELECT 135, 13, 13, 'void', 'succeeded', amount_cents, 131, 'void_demo_135', 'seed-ptx-135', '2026-11-12T16:00:00Z', '2026-11-12T16:00:03Z'
FROM payments WHERE payment_id = 13;

-- O-18: customer's bank opened a chargeback; pending, so no refund may be issued (RF-R5).
INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents,
                                  processor_reference, idempotency_key, created_at, processed_at)
SELECT 188, 18, 18, 'chargeback', 'pending', amount_cents, 'cb_demo_188', 'seed-ptx-188', '2026-10-15T14:00:00Z', NULL
FROM payments WHERE payment_id = 18;

-- Gift card ledger (activation, then redemption on O-6).
INSERT INTO gift_card_transactions (gift_card_txn_id, gift_card_id, entry_type, amount_cents, payment_id, refund_id, created_at) VALUES
 (1,1,'activation',15000,NULL,NULL,'2026-09-01T15:00:00Z'),
 (2,2,'activation', 5000,NULL,NULL,'2026-10-10T15:00:00Z'),
 (3,3,'activation',20000,NULL,NULL,'2026-11-17T03:40:00Z'),
 (4,1,'redemption',-10000,21,NULL,'2026-10-26T22:00:00Z');

-- -----------------------------------------------------------------------------
-- 12. Returns, evidence, refunds (partial returns / partial refunds)
-- -----------------------------------------------------------------------------
INSERT INTO returns (return_id, rma_number, order_id, customer_id, status, eligibility, ineligible_reason, remedy, return_method,
                     initiated_via, customer_notes, decided_by_type, decided_by_staff_id, requested_at, decided_at, received_at, closed_at) VALUES
 (1,'RMA-300001', 2, 2,'completed','auto_approved',NULL,'refund_original_payment','not_required','chat_agent',
    'Champagne bottle shattered in the bag','ai_agent',NULL,'2026-10-04T13:00:00Z','2026-10-04T13:10:00Z',NULL,'2026-10-04T13:15:00Z'),
 (2,'RMA-300002', 4, 4,'completed','auto_approved',NULL,'refund_original_payment','not_required','chat_agent',
    'One bottle is Galil Merlot, not the Cabernet I ordered','ai_agent',NULL,'2026-11-09T15:00:00Z','2026-11-09T15:05:00Z',NULL,'2026-11-09T15:06:00Z'),
 (3,'RMA-300003', 6, 6,'completed','auto_approved',NULL,'store_credit','in_store_dropoff','chat_agent',
    'Pauillac smells of wet cardboard; bottle 90% full, cork reinserted','ai_agent',NULL,'2026-11-01T15:00:00Z','2026-11-01T15:08:00Z','2026-11-03T18:00:00Z','2026-11-03T18:30:00Z'),
 (4,'RMA-300004',11, 1,'completed','auto_approved',NULL,'refund_original_payment','in_store_dropoff','chat_agent',
    'Ordered too much Napa Cab for the party; 2 bottles unopened','ai_agent',NULL,'2026-11-04T16:00:00Z','2026-11-04T16:01:00Z','2026-11-06T18:00:00Z','2026-11-06T18:30:00Z'),
 (5,'RMA-300005',16, 3,'needs_review','needs_review',NULL,'refund_original_payment','not_required','chat_agent',
    'Box arrived soaked, both bottles broken','ai_agent',NULL,'2026-11-13T22:00:00Z',NULL,NULL,NULL),
 (6,'RMA-300006',18,10,'rejected','ineligible','A-35: the NY Store does not accept change-of-mind returns','refund_original_payment','not_required','chat_agent',
    'Changed my mind about the tequila','ai_agent',NULL,'2026-09-25T17:00:00Z','2026-09-25T17:02:00Z',NULL,'2026-09-25T17:02:00Z');

INSERT INTO return_items (return_item_id, return_id, order_id, order_item_id, quantity, reason_code, item_condition, disposition, restocking_fee_bps, inspection_notes) VALUES
 (1,1, 2, 4,1,'broken_on_arrival','broken','destroy',0,'Photo shows shattered bottle; no return needed (A-30)'),
 (2,2, 4,10,1,'wrong_item','unopened','customer_keeps',0,'Picking error; customer keeps the wrong bottle (A-31)'),
 (3,3, 6,15,1,'corked_or_flawed','defective','return_to_vendor',0,'TCA confirmed by store sommelier'),
 (4,4,11,26,2,'change_of_mind','unopened','restock',1500,'Seals intact; resaleable'),
 (5,5,16,32,2,'damaged_in_transit','broken','pending',0,'Awaiting finance approval (> $150)'),
 (6,6,18,36,1,'change_of_mind','unopened','pending',0,NULL);

INSERT INTO return_evidence (evidence_id, return_id, return_item_id, evidence_type, storage_ref, uploaded_at) VALUES
 (1,1,1,'photo','evidence/2026/10/RMA-300001-1.jpg','2026-10-04T13:06:00Z'),
 (2,3,3,'photo','evidence/2026/11/RMA-300003-1.jpg','2026-11-01T15:05:00Z'),
 (3,5,5,'photo','evidence/2026/11/RMA-300005-1.jpg','2026-11-13T22:10:00Z'),
 (4,5,5,'photo','evidence/2026/11/RMA-300005-2.jpg','2026-11-13T22:11:00Z'),
 (5,5,NULL,'carrier_report','evidence/2026/11/RMA-300005-ups-damage-report.pdf','2026-11-14T15:00:00Z');

-- Amounts: items + tax (+ shipping) - restocking fee. Line taxes come from order_items.tax_cents.
INSERT INTO refunds (refund_id, refund_number, order_id, return_id, reason_code, method, status, items_amount_cents, tax_amount_cents,
                     shipping_amount_cents, tip_amount_cents, restocking_fee_cents, amount_cents, requires_human_approval, approved_by_staff_id,
                     initiated_by_type, initiated_by_ref, idempotency_key, note, created_at, approved_at, completed_at) VALUES
 (1,'RF-400001', 2,1,'broken_on_arrival','original_payment','succeeded', 6100, 541,   0,0,   0, 6641,0,NULL,'ai_agent','wines-ai-agent','seed-rf-1',
    'Full line refund incl. tax (A-30)','2026-10-04T13:12:00Z','2026-10-04T13:12:00Z','2026-10-04T13:13:00Z'),
 (2,'RF-400002', 4,2,'wrong_item','original_payment','succeeded',       2700, 239,   0,0,   0, 2939,0,NULL,'ai_agent','wines-ai-agent','seed-rf-2',
    '1 of 3 units; customer keeps wrong bottle','2026-11-09T15:05:00Z','2026-11-09T15:05:00Z','2026-11-09T15:06:00Z'),
 (3,'RF-400003', 6,3,'corked_or_flawed','store_credit','succeeded',     9900, 829,   0,0,   0,10729,0,NULL,'ai_agent','wines-ai-agent','seed-rf-3',
    'Customer chose instant store credit','2026-11-01T15:10:00Z','2026-11-01T15:10:00Z','2026-11-01T15:10:00Z'),
 (4,'RF-400004',10,NULL,'failed_delivery','original_payment','succeeded',6800, 604,   0,0,   0, 7404,0,NULL,'system','order-service','seed-rf-4',
    'Two failed deliveries (A-17): products + tax refunded, delivery fee retained','2026-10-31T16:00:00Z','2026-10-31T16:00:00Z','2026-10-31T16:02:00Z'),
 (5,'RF-400005',11,4,'change_of_mind','original_payment','succeeded',   9600, 541,   0,0,1440, 8701,0,NULL,'ai_agent','wines-ai-agent','seed-rf-5',
    'NJ change-of-mind to card: 15% restocking fee (A-34); tax on refunded amount','2026-11-06T18:30:00Z','2026-11-06T18:30:00Z','2026-11-06T18:31:00Z'),
 (6,'RF-400006',12,NULL,'price_match','original_payment','succeeded',    602,  53,   0,0,   0,  655,1,7,'staff','S-1007','seed-rf-6',
    'Approved price match PM-600001: $3.01 x 2 + tax','2026-11-12T19:00:00Z','2026-11-12T19:00:00Z','2026-11-12T19:01:00Z'),
 (7,'RF-400007',16,5,'damaged_in_transit','original_payment','pending_approval',19000,1259,1598,0,0,21857,1,NULL,'ai_agent','wines-ai-agent','seed-rf-7',
    'Whole order affected: products, tax, and shipping fee incl. its tax. Over $150 agent limit (A-60) -> finance approval','2026-11-13T22:15:00Z',NULL,NULL);

INSERT INTO refund_items (refund_id, order_id, order_item_id, quantity, amount_cents) VALUES
 (1, 2, 4,1, 6641),
 (2, 4,10,1, 2939),
 (3, 6,15,1,10729),
 (4,10,23,3, 5226),(4,10,24,1,2178),
 (5,11,26,2, 8701),
 (6,12,27,0,  655),
 (7,16,32,2,20259);

-- Money movement for card refunds (parent = the capture being refunded).
INSERT INTO payment_transactions (transaction_id, payment_id, order_id, transaction_type, status, amount_cents, parent_transaction_id,
                                  refund_id, processor_reference, idempotency_key, created_at, processed_at)
SELECT p.payment_id * 10 + 6, p.payment_id, f.order_id, 'refund', 'succeeded', f.amount_cents, p.payment_id * 10 + 2,
       f.refund_id, 're_demo_' || f.refund_id, 'seed-ptx-' || (p.payment_id * 10 + 6), f.created_at, f.completed_at
FROM refunds f JOIN payments p ON p.order_id = f.order_id AND p.tender_type IN ('card','apple_pay','google_pay')
WHERE f.method = 'original_payment' AND f.status = 'succeeded';

-- -----------------------------------------------------------------------------
-- 13. Store credit and loyalty ledgers
-- -----------------------------------------------------------------------------
INSERT INTO store_credit_transactions (store_credit_txn_id, customer_id, entry_type, amount_cents, order_id, refund_id, payment_id, reason, issued_by_type, issued_by_ref, created_at) VALUES
 (1,1,'issue_goodwill',  500,NULL,NULL,NULL,'Missed delivery window (June)','staff','S-1001','2026-06-01T16:00:00Z'),
 (2,6,'issue_refund',  10729,   6,   3,NULL,'Corked bottle refund as store credit (RF-400003)','ai_agent','wines-ai-agent','2026-11-01T15:10:00Z'),
 (3,4,'issue_goodwill', 1000,   4,NULL,NULL,'Goodwill: delivery 85 minutes after window (A-61)','ai_agent','wines-ai-agent','2026-11-09T15:06:00Z'),
 (4,4,'redeem',        -1000,  20,NULL,  22,'Applied at checkout on WA-100120','system','checkout-service','2026-11-19T20:40:00Z');

INSERT INTO loyalty_accounts (customer_id, tier, status, enrolled_at, tier_updated_at) VALUES
 (1,'insider','active','2025-03-02T15:20:00Z','2026-08-01T05:00:00Z'),(2,'member','active','2025-05-19T19:45:00Z','2025-05-19T19:45:00Z'),
 (3,'member','active','2025-07-08T12:00:00Z','2025-07-08T12:00:00Z'),(4,'member','active','2025-09-14T21:10:00Z','2025-09-14T21:10:00Z'),
 (5,'member','active','2026-01-10T17:25:00Z','2026-01-10T17:25:00Z'),(6,'insider','active','2024-11-30T16:00:00Z','2025-03-01T05:00:00Z'),
 (7,'member','active','2024-12-12T18:30:00Z','2024-12-12T18:30:00Z'),(10,'member','active','2025-08-01T23:00:00Z','2025-08-01T23:00:00Z'),
 (12,'member','active','2025-04-22T20:00:00Z','2025-04-22T20:00:00Z');

INSERT INTO loyalty_rewards (reward_id, customer_id, value_cents, points_cost, status, issued_at, expires_at, redeemed_order_id, redeemed_at) VALUES
 (1,7,1000,250,'redeemed', '2026-09-30T12:00:00Z','2026-12-29T12:00:00Z',17,'2026-10-18T17:00:00Z'),
 (2,1,1000,250,'available','2026-11-01T12:00:00Z','2027-01-30T12:00:00Z',NULL,NULL),
 (3,3,1000,250,'expired',  '2026-08-01T12:00:00Z','2026-10-30T12:00:00Z',NULL,NULL);

-- Points: 1 per $1 of product subtotal after discounts; Insider earns 1.25x (A-53).
INSERT INTO loyalty_point_transactions (customer_id, entry_type, points, order_id, reason, created_by_type, created_at)
SELECT o.customer_id, 'earn',
       ((o.items_subtotal_cents - o.discount_total_cents) / 100) * CASE la.tier WHEN 'insider' THEN 125 ELSE 100 END / 100,
       o.order_id, 'Order ' || o.order_number, 'system', o.completed_at
FROM orders o JOIN loyalty_accounts la ON la.customer_id = o.customer_id
WHERE o.status = 'completed'
ORDER BY o.completed_at;

INSERT INTO loyalty_point_transactions (customer_id, entry_type, points, order_id, reward_id, reason, created_by_type, created_at) VALUES
 (7,'adjustment',        300,NULL,NULL,'Points migrated from legacy program','system','2026-01-15T12:00:00Z'),
 (3,'adjustment',        260,NULL,NULL,'Points migrated from legacy program','system','2026-02-01T12:00:00Z'),
 (7,'convert_to_reward',-250,NULL,1,'250 points -> $10 reward','system','2026-09-30T12:00:00Z'),
 (3,'convert_to_reward',-250,NULL,3,'250 points -> $10 reward','system','2026-08-01T12:00:00Z'),
 (1,'convert_to_reward',-250,NULL,2,'250 points -> $10 reward','system','2026-11-01T12:00:00Z'),
 (1,'reversal',         -120,  11,NULL,'Points reversed for returned items (RMA-300004)','system','2026-11-06T18:31:00Z');

-- -----------------------------------------------------------------------------
-- 14. Reservations and the inventory ledger (reconciles to inventory_levels)
-- -----------------------------------------------------------------------------
-- Consumed: units that left a warehouse on a shipment or pickup.
INSERT INTO inventory_reservations (order_id, order_item_id, warehouse_id, variant_id, quantity, status, expires_at, created_at, closed_at)
SELECT si.order_id, si.order_item_id, s.warehouse_id, i.variant_id, si.quantity, 'consumed', NULL, o.placed_at, s.shipped_at
FROM shipment_items si
JOIN shipments s ON s.shipment_id = si.shipment_id
JOIN order_items i ON i.order_item_id = si.order_item_id
JOIN orders o ON o.order_id = si.order_id
WHERE s.shipped_at IS NOT NULL;

INSERT INTO inventory_reservations (order_id, order_item_id, warehouse_id, variant_id, quantity, status, expires_at, created_at, closed_at) VALUES
 (5,11,1,33,2,'active','2026-11-25T21:00:00Z','2026-11-18T19:30:00Z',NULL),
 (5,12,1,34,2,'active','2026-11-25T21:00:00Z','2026-11-18T19:30:00Z',NULL),
 (5,13,1,35,2,'active','2026-11-25T21:00:00Z','2026-11-18T19:30:00Z',NULL),
 (8,19,4,27,6,'active',NULL,'2026-11-17T03:30:00Z',NULL),
 (8,20,4,36,6,'active',NULL,'2026-11-17T03:30:00Z',NULL),
 (9,21,1,17,4,'active','2026-11-26T14:25:00Z','2026-11-19T14:25:00Z',NULL),
 (9,22,1,18,1,'active','2026-11-26T14:25:00Z','2026-11-19T14:25:00Z',NULL),
 (19,37,2,8,1,'active',NULL,'2026-11-17T14:00:00Z',NULL),
 (19,38,2,9,2,'active',NULL,'2026-11-17T14:00:00Z',NULL),
 (13,28,3,23,2,'released',NULL,'2026-11-12T15:30:00Z','2026-11-12T16:00:00Z'),
 (14,30,1,5,1,'released',NULL,'2026-11-14T15:00:00Z','2026-11-14T19:50:00Z');

UPDATE inventory_levels SET qty_reserved = COALESCE((
    SELECT SUM(r.quantity) FROM inventory_reservations r
    WHERE r.warehouse_id = inventory_levels.warehouse_id AND r.variant_id = inventory_levels.variant_id AND r.status = 'active'), 0);

-- Movements: receipts, sales, restocks. initial_load is back-solved last so
-- SUM(quantity_delta) per warehouse x variant equals qty_on_hand.
INSERT INTO inventory_movements (warehouse_id, variant_id, movement_type, quantity_delta, reference_type, reference_id, note, created_by_staff_id, created_at) VALUES
 (2,30,'receipt',12,'purchase_receipt',7001,'Distributor delivery: Mosel Kabinett restock (fills WA-100103 backorder)',4,'2026-11-16T15:00:00Z');

INSERT INTO inventory_movements (warehouse_id, variant_id, movement_type, quantity_delta, reference_type, reference_id, note, created_by_staff_id, created_at)
SELECT s.warehouse_id, i.variant_id, 'sale_shipment', -si.quantity, 'shipment', s.shipment_id, 'Shipped ' || s.shipment_number, NULL, s.shipped_at
FROM shipment_items si JOIN shipments s ON s.shipment_id = si.shipment_id JOIN order_items i ON i.order_item_id = si.order_item_id
WHERE s.shipped_at IS NOT NULL
ORDER BY s.shipped_at;

INSERT INTO inventory_movements (warehouse_id, variant_id, movement_type, quantity_delta, reference_type, reference_id, note, created_by_staff_id, created_at) VALUES
 (3,28,'return_restock',3,'shipment',9,'Undeliverable order WA-100110 returned to shelf',5,'2026-10-31T16:05:00Z'),
 (3,25,'return_restock',1,'shipment',9,'Undeliverable order WA-100110 returned to shelf',5,'2026-10-31T16:05:00Z'),
 (1,20,'return_restock',2,'return',4,'RMA-300004 unopened bottles restocked',4,'2026-11-06T18:20:00Z');

INSERT INTO inventory_movements (warehouse_id, variant_id, movement_type, quantity_delta, reference_type, reference_id, note, created_by_staff_id, created_at)
SELECT il.warehouse_id, il.variant_id, 'initial_load',
       il.qty_on_hand - COALESCE((SELECT SUM(m.quantity_delta) FROM inventory_movements m
                                  WHERE m.warehouse_id = il.warehouse_id AND m.variant_id = il.variant_id), 0),
       'count', 2026, 'Opening balance from POS migration', 8, '2026-01-01T05:00:00Z'
FROM inventory_levels il
WHERE il.qty_on_hand - COALESCE((SELECT SUM(m.quantity_delta) FROM inventory_movements m
                                 WHERE m.warehouse_id = il.warehouse_id AND m.variant_id = il.variant_id), 0) > 0;

-- -----------------------------------------------------------------------------
-- 15. Carts and price-match requests
-- -----------------------------------------------------------------------------
INSERT INTO carts (cart_id, cart_token, customer_id, store_id, status, fulfillment_type, promo_code, converted_order_id, created_at, updated_at, expires_at) VALUES
 (1,'cart_demo_0001',1,1,'active','local_delivery','FALL10',NULL,'2026-11-18T22:00:00Z','2026-11-18T22:20:00Z','2026-12-18T22:00:00Z'),
 (2,'cart_demo_0002',2,2,'abandoned','local_delivery',NULL,NULL,'2026-11-12T16:05:00Z','2026-11-12T16:10:00Z','2026-11-19T16:05:00Z'),
 (3,'cart_demo_0003',9,1,'converted','local_delivery','WELCOME10',9,'2026-11-19T14:00:00Z','2026-11-19T14:25:00Z',NULL),
 (4,'cart_demo_0004',3,1,'active','shipping',NULL,NULL,'2026-11-18T19:00:00Z','2026-11-18T19:05:00Z','2026-12-18T19:00:00Z');

INSERT INTO cart_items (cart_id, variant_id, quantity, added_at) VALUES
 (1, 5,2,'2026-11-18T22:00:00Z'),(1,12,3,'2026-11-18T22:05:00Z'),(1, 7,1,'2026-11-18T22:20:00Z'),
 (2,29,2,'2026-11-12T16:05:00Z'),
 (3,17,4,'2026-11-19T14:00:00Z'),(3,18,1,'2026-11-19T14:02:00Z'),
 (4,16,3,'2026-11-18T19:00:00Z');   -- exceeds NJ allocation of 2: cart warning

INSERT INTO price_match_requests (price_match_id, request_number, customer_id, store_id, variant_id, order_id, competitor_name, competitor_state,
                                  competitor_url_or_proof, competitor_price_cents, our_price_cents, quantity, status, decision_reason,
                                  reviewed_by_staff_id, created_at, decided_at) VALUES
 (1,'PM-600001',12,2,27,12,'Gramercy Wine Cellar (demo)','NY','https://competitor.example.com/rioja-reserva-2019',2599,2900,2,'approved',
    'Identical item, NY licensed retailer, in stock, publicly listed (A-43)',7,'2026-11-12T15:00:00Z','2026-11-12T19:00:00Z'),
 (2,'PM-600002', 1,1, 7,NULL,'Online Marketplace (demo)','NJ','https://marketplace.example.com/listing/88213',4499,5800,6,'rejected',
    'Marketplace pricing is excluded (A-43)',7,'2026-11-05T17:00:00Z','2026-11-05T18:00:00Z'),
 (3,'PM-600003', 3,1,24,NULL,'Princeton Wine Shop (demo)','NJ','https://competitor.example.org/willamette-pinot-2022',3899,4200,3,'pending_review',
    NULL,NULL,'2026-11-18T20:00:00Z',NULL);

-- -----------------------------------------------------------------------------
-- 16. Support tickets and messages
-- -----------------------------------------------------------------------------
INSERT INTO support_tickets (ticket_id, ticket_number, customer_id, order_id, return_id, conversation_id, channel, category, priority, reason_code, status,
                             subject, summary, customer_sentiment, assigned_team, assigned_staff_id, sla_due_at, first_response_at, resolved_at, closed_at,
                             csat_score, created_by_type, created_at, updated_at) VALUES
 (1,'TKT-500001', 2, 2,1,'conv-demo-0001','chat_agent','damaged_item','P3',NULL,'closed',
    'Broken Champagne bottle on arrival','Bottle shattered in delivery bag. Photo received; claim auto-approved; RF-400001 $66.41 refunded to Amex ending 1005.',
    'frustrated','support',NULL,'2026-10-05T13:00:00Z','2026-10-04T13:00:00Z','2026-10-04T13:15:00Z','2026-10-07T13:15:00Z',5,'ai_agent','2026-10-04T13:00:00Z','2026-10-07T13:15:00Z'),
 (2,'TKT-500002', 4, 4,2,'conv-demo-0002','chat_agent','wrong_or_missing_item','P3',NULL,'resolved',
    'Late delivery and one wrong bottle','Delivered 85 min late; 1 of 3 bottles was the wrong wine. Refunded 1 bottle (RF-400002) and issued $10 goodwill credit.',
    'frustrated','support',NULL,'2026-11-10T15:00:00Z','2026-11-09T15:00:00Z','2026-11-09T15:10:00Z',NULL,4,'ai_agent','2026-11-09T15:00:00Z','2026-11-09T15:10:00Z'),
 (3,'TKT-500003', 6, 6,3,'conv-demo-0003','chat_agent','flawed_wine','P3',NULL,'resolved',
    'Corked bottle of Pauillac','Corked 2019 Pauillac (90% full). Customer chose store credit; RF-400003 $107.29 issued as credit; bottle dropped off for distributor credit.',
    'neutral','support',NULL,'2026-11-02T15:00:00Z','2026-11-01T15:00:00Z','2026-11-03T18:30:00Z',NULL,NULL,'ai_agent','2026-11-01T15:00:00Z','2026-11-03T18:30:00Z'),
 (4,'TKT-500004', 7, 7,NULL,'conv-demo-0004','chat_agent','delivery_issue','P3',NULL,'pending_customer',
    'Gift delivery missed: no adult to sign','UPS attempt 1 of 3 failed (no 21+ adult). Asked customer to confirm recipient availability or redirect to a UPS Access Point.',
    'neutral','fulfillment',NULL,'2026-11-20T15:00:00Z','2026-11-19T13:00:00Z',NULL,NULL,NULL,'ai_agent','2026-11-19T13:00:00Z','2026-11-19T13:05:00Z'),
 (5,'TKT-500005', 8, 8,NULL,'conv-demo-0005','chat_agent','fraud','P1','account_takeover','escalated',
    'Possible account takeover','Customer did not place WA-100108; new device changed email and address. Account locked (lock_account), order held, gift card frozen. Live handoff to compliance.',
    'angry','compliance',6,'2026-11-17T04:20:00Z','2026-11-17T04:06:00Z',NULL,NULL,NULL,'ai_agent','2026-11-17T04:00:00Z','2026-11-17T04:10:00Z'),
 (6,'TKT-500006', 9, 9,NULL,'conv-demo-0006','chat_agent','age_verification','P3',NULL,'pending_customer',
    'Why do I need to verify my ID?','First order requires ID verification (A-05). Explained; resent verification link.',
    'neutral','support',NULL,'2026-11-20T14:30:00Z','2026-11-19T14:31:00Z',NULL,NULL,NULL,'ai_agent','2026-11-19T14:30:00Z','2026-11-19T14:31:00Z'),
 (7,'TKT-500007',10,10,NULL,NULL,'email','refund_status','P3',NULL,'closed',
    'Where is my refund for the cancelled order?','RF-400004 $74.04 issued 2026-10-31 to Mastercard ending 4520; delivery fee retained per A-17; 5-10 business days to post.',
    'frustrated','support',2,'2026-11-04T14:00:00Z','2026-11-03T15:00:00Z','2026-11-03T16:00:00Z','2026-11-06T16:00:00Z',3,'customer','2026-11-03T14:00:00Z','2026-11-06T16:00:00Z'),
 (8,'TKT-500008',12,12,NULL,NULL,'web_form','price_match','P2','price_match','closed',
    'Price match: Rioja Reserva 2019','Approved PM-600001 within 7 days of purchase; RF-400006 $6.55 refunded to original card.',
    'positive','pricing',7,'2026-11-12T19:00:00Z','2026-11-12T16:00:00Z','2026-11-12T19:00:00Z','2026-11-15T19:00:00Z',5,'customer','2026-11-12T15:00:00Z','2026-11-15T19:00:00Z'),
 (9,'TKT-500009', 3,16,5,'conv-demo-0009','chat_agent','damaged_item','P2','refund_over_limit','escalated',
    'Two broken Pauillac bottles ($218.57)','Both bottles broken in transit; photos + UPS damage report on file. Refund RF-400007 exceeds agent limit (A-60) and awaits finance approval.',
    'frustrated','finance',3,'2026-11-14T18:00:00Z','2026-11-13T22:05:00Z',NULL,NULL,NULL,'ai_agent','2026-11-13T22:05:00Z','2026-11-14T15:00:00Z'),
 (10,'TKT-500010',10,18,NULL,NULL,'email','payment_issue','P2',NULL,'pending_internal',
    'Bank dispute on order WA-100118','Chargeback opened by issuing bank; order was delivered with ID check. Finance preparing evidence; no refund while dispute is open (RF-R5).',
    'neutral','finance',3,'2026-10-15T19:00:00Z','2026-10-15T16:00:00Z',NULL,NULL,NULL,'system','2026-10-15T15:00:00Z','2026-10-15T16:00:00Z'),
 (11,'TKT-500011',11,NULL,NULL,'conv-demo-0011','chat_agent','privacy_request','P2','privacy_request','open',
    'Request for a copy of my personal data','Data access request (A-72). Identity verified via OTP; due within 15 days (legal max 45).',
    'neutral','privacy',6,'2026-12-02T15:00:00Z','2026-11-17T15:05:00Z',NULL,NULL,NULL,'ai_agent','2026-11-17T15:00:00Z','2026-11-17T15:05:00Z'),
 (12,'TKT-500012', 6,NULL,NULL,NULL,'email','product_request','P3','product_request','open',
    'Special order: 30 Year Old Tawny Port','Customer asks for 6 bottles of the 30 Year Tawny (not carried). Catalog checking distributor availability.',
    'positive','catalog',8,'2026-11-11T14:00:00Z','2026-11-10T18:00:00Z',NULL,NULL,NULL,'customer','2026-11-10T14:00:00Z','2026-11-10T18:00:00Z'),
 (13,'TKT-500013',NULL,NULL,NULL,'conv-demo-0013','chat_agent','general','P3','kb_gap','new',
    'Private tasting for 20 people?','Unauthenticated visitor asked about hosting a private tasting; KB has no capacity info. Routed to events team.',
    'positive','events',NULL,'2026-11-20T02:00:00Z',NULL,NULL,NULL,NULL,'ai_agent','2026-11-19T02:00:00Z','2026-11-19T02:00:00Z');

INSERT INTO ticket_messages (ticket_id, author_type, author_customer_id, author_staff_id, visibility, body, attachment_refs, created_at) VALUES
 (1,'customer',2,NULL,'public','My Champagne bottle arrived shattered. The bag is soaked.',NULL,'2026-10-04T13:00:00Z'),
 (1,'ai_agent',NULL,NULL,'public','I''m sorry about that. Could you upload a photo with this secure link? You don''t need to return the broken glass.',NULL,'2026-10-04T13:01:00Z'),
 (1,'customer',2,NULL,'public','Uploaded.','["evidence/2026/10/RMA-300001-1.jpg"]','2026-10-04T13:06:00Z'),
 (1,'ai_agent',NULL,NULL,'public','Thanks. I''ve refunded $66.41 to your Amex ending 1005. Banks usually take 5-10 business days to post it.',NULL,'2026-10-04T13:13:00Z'),
 (2,'customer',4,NULL,'public','Delivery came almost 1.5 hours late and one bottle is Merlot, not the Cabernet.',NULL,'2026-11-09T15:00:00Z'),
 (2,'ai_agent',NULL,NULL,'public','Apologies for both. I refunded one bottle ($29.39) to your Visa ending 2384; please keep the Merlot. I also added a $10 store credit for the late delivery.',NULL,'2026-11-09T15:07:00Z'),
 (2,'system',NULL,NULL,'internal','Picking error logged for NY-CHE-FLOOR bin FL-32 (S-1005 notified).',NULL,'2026-11-09T15:10:00Z'),
 (3,'customer',6,NULL,'public','The 2019 Pauillac smells like wet cardboard.',NULL,'2026-11-01T15:00:00Z'),
 (3,'ai_agent',NULL,NULL,'public','That sounds like cork taint. Would you like a refund to your card (5-10 business days) or instant store credit?',NULL,'2026-11-01T15:04:00Z'),
 (3,'customer',6,NULL,'public','Store credit is fine.',NULL,'2026-11-01T15:08:00Z'),
 (3,'staff',NULL,5,'internal','Bottle received at Chelsea; TCA confirmed. Sent to distributor for credit.',NULL,'2026-11-03T18:30:00Z'),
 (4,'customer',7,NULL,'public','UPS says nobody was there to sign for my sister''s birthday gift.',NULL,'2026-11-19T13:00:00Z'),
 (4,'ai_agent',NULL,NULL,'public','UPS will try again next business day (up to 3 attempts). An adult 21+ must sign. You can also redirect it to a UPS Access Point with the tracking link.',NULL,'2026-11-19T13:05:00Z'),
 (5,'customer',8,NULL,'public','I did not place this order and my email was changed!',NULL,'2026-11-17T04:00:00Z'),
 (5,'ai_agent',NULL,NULL,'public','I''ve locked your account to protect it and connected you with our security team now.',NULL,'2026-11-17T04:06:00Z'),
 (5,'staff',NULL,6,'internal','Confirmed new-device session from unfamiliar IP. Order held, gift card GC-9921 frozen. Awaiting identity documents.',NULL,'2026-11-17T04:10:00Z'),
 (6,'customer',9,NULL,'public','Why do I need to verify my ID? I already gave my birthday.',NULL,'2026-11-19T14:30:00Z'),
 (6,'ai_agent',NULL,NULL,'public','Because we sell alcohol, first orders need a quick ID check before release. Here''s a fresh secure link; it takes about two minutes.',NULL,'2026-11-19T14:31:00Z'),
 (7,'customer',10,NULL,'public','My order was cancelled. Where is my money?',NULL,'2026-11-03T14:00:00Z'),
 (7,'staff',NULL,2,'public','Your refund of $74.04 was issued on Oct 31 to your Mastercard ending 4520. The $9.99 delivery fee was kept after two attempts, per our policy.',NULL,'2026-11-03T15:00:00Z'),
 (8,'customer',12,NULL,'public','Gramercy Wine Cellar has the 2019 Rioja Reserva for $25.99.','["https://competitor.example.com/rioja-reserva-2019"]','2026-11-12T15:00:00Z'),
 (8,'staff',NULL,7,'public','Verified and approved. We refunded the $3.01 difference per bottle plus tax ($6.55).',NULL,'2026-11-12T19:00:00Z'),
 (9,'customer',3,NULL,'public','Both bottles arrived broken and the box is soaked.',NULL,'2026-11-13T22:05:00Z'),
 (9,'ai_agent',NULL,NULL,'public','I''m sorry. I''ve opened a claim and sent it to our finance team because of the amount. They respond within 4 business hours.',NULL,'2026-11-13T22:16:00Z'),
 (9,'system',NULL,NULL,'internal','refund RF-400007 requires_human_approval (A-60: $218.57 > $150).',NULL,'2026-11-13T22:16:00Z'),
 (10,'system',NULL,NULL,'internal','Chargeback cb_demo_188 received for payment 18 ($105.60). Reason: unrecognized transaction.',NULL,'2026-10-15T15:00:00Z'),
 (10,'staff',NULL,3,'internal','Pulled delivery proof (ID checked, courier SH-200015). Preparing representment.',NULL,'2026-10-15T16:00:00Z'),
 (11,'customer',11,NULL,'public','I''d like a copy of all the data you hold about me.',NULL,'2026-11-17T15:00:00Z'),
 (11,'ai_agent',NULL,NULL,'public','I''ve submitted your data access request. We''ll send it within 15 days and keep you updated.',NULL,'2026-11-17T15:05:00Z'),
 (12,'customer',6,NULL,'public','Can you get me six bottles of the Quinta do Rio Alto 30 Year Tawny?',NULL,'2026-11-10T14:00:00Z'),
 (12,'staff',NULL,8,'public','Checking with the importer now; special orders are prepaid and final sale.',NULL,'2026-11-10T18:00:00Z'),
 (13,'ai_agent',NULL,NULL,'internal','KB gap: no private-tasting capacity info for either store. Routed to events.',NULL,'2026-11-19T02:00:00Z');

-- -----------------------------------------------------------------------------
-- 17. Audit log (what the API layer will write for every sensitive read/write)
-- -----------------------------------------------------------------------------
INSERT INTO audit_logs (occurred_at, actor_type, actor_ref, action, entity_type, entity_id, customer_id, outcome, reason,
                        conversation_id, request_id, idempotency_key, before_state, after_state) VALUES
 ('2026-10-04T13:00:30.000Z','ai_agent','wines-ai-agent','customer.verify_identity','customer','C-100002',2,'success','OTP via SMS','conv-demo-0001','req-0001',NULL,NULL,json_object('verified',1)),
 ('2026-10-04T13:01:00.000Z','ai_agent','wines-ai-agent','order.view','order','WA-100102',2,'success',NULL,'conv-demo-0001','req-0002',NULL,NULL,NULL),
 ('2026-10-04T13:10:00.000Z','ai_agent','wines-ai-agent','return.create','return','RMA-300001',2,'success','broken_on_arrival','conv-demo-0001','req-0003','seed-rma-1',NULL,json_object('eligibility','auto_approved')),
 ('2026-10-04T13:12:00.000Z','ai_agent','wines-ai-agent','refund.issue','refund','RF-400001',2,'success','within A-60 authority','conv-demo-0001','req-0004','seed-rf-1',NULL,json_object('amount_cents',6641,'method','original_payment')),
 ('2026-10-21T21:31:00.000Z','staff','S-1005','shipment.update_status','shipment','SH-200009',10,'success','delivery_failed',NULL,'req-0010',NULL,json_object('status','out_for_delivery'),json_object('status','delivery_failed')),
 ('2026-10-22T14:00:00.000Z','ai_agent','wines-ai-agent','order.reschedule_delivery','order','WA-100110',10,'success','free redelivery (A-17)','conv-demo-0007','req-0011','seed-resched-10',NULL,json_object('window','2026-10-23T20:00Z/22:00Z')),
 ('2026-10-31T16:00:00.000Z','system','order-service','order.cancel','order','WA-100110',10,'success','pickup hold expired',NULL,'req-0012',NULL,json_object('status','returned_to_store'),json_object('status','cancelled')),
 ('2026-10-31T16:00:30.000Z','system','order-service','refund.issue','refund','RF-400004',10,'success','failed_delivery',NULL,'req-0013','seed-rf-4',NULL,json_object('amount_cents',7404)),
 ('2026-11-01T15:10:00.000Z','ai_agent','wines-ai-agent','refund.issue','refund','RF-400003',6,'success','corked_or_flawed; store credit','conv-demo-0003','req-0020','seed-rf-3',NULL,json_object('amount_cents',10729,'method','store_credit')),
 ('2026-11-04T16:01:00.000Z','ai_agent','wines-ai-agent','return.create','return','RMA-300004',1,'success','NJ change of mind within 14 days (A-34)','conv-demo-0014','req-0030','seed-rma-4',NULL,json_object('restocking_fee_bps',1500)),
 ('2026-11-05T18:00:00.000Z','staff','S-1007','price_match.reject','price_match','PM-600002',1,'success','marketplace excluded (A-43)',NULL,'req-0031',NULL,json_object('status','pending_review'),json_object('status','rejected')),
 ('2026-11-06T18:30:00.000Z','ai_agent','wines-ai-agent','refund.issue','refund','RF-400005',1,'success','restocking fee applied','conv-demo-0014','req-0032','seed-rf-5',NULL,json_object('amount_cents',8701)),
 ('2026-11-09T15:05:00.000Z','ai_agent','wines-ai-agent','refund.issue','refund','RF-400002',4,'success','wrong_item','conv-demo-0002','req-0040','seed-rf-2',NULL,json_object('amount_cents',2939)),
 ('2026-11-09T15:06:00.000Z','ai_agent','wines-ai-agent','store_credit.issue_goodwill','customer','C-100004',4,'success','late delivery; first goodwill in 90 days (A-61)','conv-demo-0002','req-0041','seed-sc-3',NULL,json_object('amount_cents',1000)),
 ('2026-11-12T16:00:00.000Z','ai_agent','wines-ai-agent','order.cancel','order','WA-100113',2,'success','customer request before picking (A-21)','conv-demo-0015','req-0050','seed-cancel-13',json_object('status','placed'),json_object('status','cancelled')),
 ('2026-11-12T19:00:00.000Z','staff','S-1007','price_match.approve','price_match','PM-600001',12,'success','A-43 criteria met',NULL,'req-0051',NULL,json_object('status','pending_review'),json_object('status','approved')),
 ('2026-11-12T19:00:30.000Z','staff','S-1007','refund.issue','refund','RF-400006',12,'success','price match difference',NULL,'req-0052','seed-rf-6',NULL,json_object('amount_cents',655)),
 ('2026-11-13T22:15:00.000Z','ai_agent','wines-ai-agent','refund.issue','refund','RF-400007',3,'requires_approval','amount over agent limit (A-60)','conv-demo-0009','req-0060','seed-rf-7',NULL,json_object('amount_cents',21857,'status','pending_approval')),
 ('2026-11-13T22:16:00.000Z','ai_agent','wines-ai-agent','ticket.escalate','support_ticket','TKT-500009',3,'success','refund_over_limit P2','conv-demo-0009','req-0061',NULL,NULL,json_object('assigned_team','finance')),
 ('2026-11-14T19:48:00.000Z','ai_agent','wines-ai-agent','order.respond_to_substitution','order_item','30',5,'success','customer declined adjacent vintage','conv-demo-0016','req-0070','seed-sub-1',json_object('status','proposed'),json_object('status','declined')),
 ('2026-11-17T03:20:00.000Z','customer','C-100008','address.create','customer_address','13',8,'success','added from new device',NULL,'req-0080',NULL,NULL,json_object('city','Hempstead','state','NY')),
 ('2026-11-17T03:31:00.000Z','system','fraud-rules','order.hold','order','WA-100108',8,'success','fraud_review',NULL,'req-0081',NULL,json_object('status','placed'),json_object('status','on_hold','hold_reason','fraud_review')),
 ('2026-11-17T04:05:00.000Z','ai_agent','wines-ai-agent','account.lock','customer','C-100008',8,'success','suspected account takeover (P1)','conv-demo-0005','req-0082','seed-lock-8',json_object('status','active'),json_object('status','locked')),
 ('2026-11-17T04:06:00.000Z','ai_agent','wines-ai-agent','refund.issue','order','WA-100108',8,'denied','agent may not refund on a P1 fraud case; escalated','conv-demo-0005','req-0083',NULL,NULL,NULL),
 ('2026-11-17T15:04:00.000Z','ai_agent','wines-ai-agent','privacy.submit_request','support_ticket','TKT-500011',11,'success','access request (A-72)','conv-demo-0011','req-0090',NULL,NULL,json_object('due_by','2026-12-02')),
 ('2026-11-18T15:00:00.000Z','system','shipping-service','order.hold','order','WA-100119',11,'success','weather (A-19)',NULL,'req-0100',NULL,json_object('status','picking'),json_object('status','on_hold','hold_reason','weather')),
 ('2026-11-19T14:31:00.000Z','ai_agent','wines-ai-agent','age_verification.start','customer','C-100009',9,'success','resent verification link','conv-demo-0006','req-0110',NULL,NULL,json_object('status','pending')),
 ('2026-11-19T14:32:00.000Z','ai_agent','wines-ai-agent','customer.view_profile','customer','C-100007',7,'denied','identity not verified (A-70)','conv-demo-0004','req-0111',NULL,NULL,NULL);
