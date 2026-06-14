"""
PDF-Grounded Fault Scenarios for Industrial Motors

Each scenario is derived from the actual motor manuals indexed in Qdrant.
All thresholds, sensor values, and recommendations trace back to specific
manual sections.
"""

FAULT_SCENARIOS = {
    "general-industrial-motor": [
        {
            "fault_code": "FC-TH-01",
            "fault_name": "Bearing Overtemperature — Drive End",
            "description": "Drive End bearing temperature has exceeded the alarm threshold, indicating possible lubrication starvation or blocked cooling airflow.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 1.9,
                "bearing_temp_drive_end_c": 112.5,
                "stator_winding_temp_c": 95,
                "stator_phase_current_a": 24.9,
                "shaft_speed_rpm": 1474,
                "bearing_lube_oil_pressure_bar": 4.2
            },
            "thresholds": {
                "bearing_temp_drive_end_c": {
                    "alarm": 110,
                    "trip": 120,
                    "citation": "Siemens SIMOTICS TN 1LA8 IOM — Section 7: Maintenance, Bearing Temperature Monitoring. Alarm: 110°C, Trip: 120°C"
                }
            },
            "risk_level": "HIGH",
            "probable_root_causes": [
                "Bearing lubrication starvation — insufficient grease quantity",
                "Blocked cooling air inlet/outlet reducing heat dissipation",
                "Bearing inner race wear due to misalignment"
            ],
            "recommended_actions": [
                "Immediately check bearing grease level via regreasing nipple — Ref: Siemens 1LA8 IOM Section 7.3 Bearing Lubrication",
                "Inspect cooling air inlet and outlet openings for blockage — Ref: Siemens 1LA8 IOM Section 2.5.1 Cooling",
                "Measure vibration at bearing housing to detect mechanical looseness — Ref: ISO 10816-3",
                "If temperature exceeds 120°C — initiate emergency shutdown — Ref: Siemens 1LA8 IOM Section 7, Trip Threshold",
                "After cooling: disassemble bearing for inspection — Ref: Siemens 1LA8 IOM Section 7.4 Bearing Maintenance"
            ]
        },
        {
            "fault_code": "FC-VB-01",
            "fault_name": "Excessive Vibration — Mechanical Imbalance",
            "description": "Vibration velocity has exceeded Zone B limit per ISO 10816-3, indicating rotor imbalance or misalignment.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 5.8,
                "bearing_temp_drive_end_c": 78,
                "stator_winding_temp_c": 88,
                "stator_phase_current_a": 27.3,
                "shaft_speed_rpm": 1468,
                "bearing_lube_oil_pressure_bar": 4.1
            },
            "thresholds": {
                "vibration_velocity_mm_s": {
                    "alarm": 4.5,
                    "trip": 7.1,
                    "citation": "ISO 10816-3 Zone B limit: 4.5 mm/s, Zone C limit: 7.1 mm/s — Referenced in Siemens 1LA8 IOM Section 5.3.3"
                }
            },
            "risk_level": "HIGH",
            "probable_root_causes": [
                "Rotor imbalance — possible loose coupling or uneven mass distribution",
                "Shaft misalignment with driven machine",
                "Bearing wear causing rotor eccentricity"
            ],
            "recommended_actions": [
                "Perform vibration spectrum analysis to distinguish imbalance from misalignment",
                "Check coupling alignment using dial indicator — Ref: Siemens 1LA8 IOM Section 5.3.4",
                "Inspect rotor for loose components or debris accumulation",
                "Rebalance rotor if imbalance confirmed — Ref: Siemens 1LA8 IOM Section 5.2.6",
                "Check bearing condition — vibration may indicate early bearing failure"
            ]
        },
        {
            "fault_code": "FC-CR-01",
            "fault_name": "Stator Current Overload",
            "description": "Stator line current exceeds rated value by more than 15%, indicating overload condition or possible phase imbalance.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 2.1,
                "bearing_temp_drive_end_c": 82,
                "stator_winding_temp_c": 108,
                "stator_phase_current_a": 32.4,
                "shaft_speed_rpm": 1441,
                "bearing_lube_oil_pressure_bar": 4.0
            },
            "thresholds": {
                "stator_phase_current_a": {
                    "alarm": "rated × 1.15",
                    "trip": "rated × 1.25",
                    "citation": "IEC EN 60034-1 / Siemens 1LA8 IOM Section 4.5 — Overload protection: thermal relay set at 1.15× rated current for SF=1.0"
                }
            },
            "risk_level": "CRITICAL",
            "probable_root_causes": [
                "Mechanical overload on driven equipment",
                "Phase voltage imbalance causing current unbalance",
                "Partial winding short circuit increasing current draw"
            ],
            "recommended_actions": [
                "Check driven machine for mechanical jam or increased load — Ref: Siemens 1LA8 IOM Section 6",
                "Measure three-phase current balance — all phases must be within 5% of each other",
                "Verify supply voltage balance at motor terminals — Ref: IEC EN 60034-1",
                "Check thermal relay setting matches motor nameplate rated current — Ref: Siemens 1LA8 IOM Section 4.5",
                "If overload persists — reduce load or investigate driven machine fault"
            ]
        },
        {
            "fault_code": "FC-LP-01",
            "fault_name": "Low Bearing Lube Oil Pressure",
            "description": "Bearing lubrication oil pressure has dropped below the minimum alarm threshold, risking bearing starvation and seizure.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 3.1,
                "bearing_temp_drive_end_c": 95,
                "stator_winding_temp_c": 92,
                "stator_phase_current_a": 25.5,
                "shaft_speed_rpm": 1472,
                "bearing_lube_oil_pressure_bar": 0.8
            },
            "thresholds": {
                "bearing_lube_oil_pressure_bar": {
                    "alarm": 1.5,
                    "trip": 1.0,
                    "citation": "Siemens 1LA8 IOM Section 7.3 — Bearing lubrication: minimum oil pressure alarm 1.5 bar, trip 1.0 bar"
                }
            },
            "risk_level": "CRITICAL",
            "probable_root_causes": [
                "Oil pump failure or reduced oil pump output",
                "Oil filter blockage causing flow restriction",
                "Oil leakage from bearing seal"
            ],
            "recommended_actions": [
                "IMMEDIATE: Check oil level in lubrication reservoir",
                "Inspect oil pump operation and outlet pressure gauge",
                "Check oil filter differential pressure — replace if blocked — Ref: Siemens 1LA8 IOM Section 7.3",
                "Inspect bearing housing seals for oil leakage",
                "If oil pressure does not recover within 2 minutes — initiate controlled shutdown to prevent bearing seizure"
            ]
        }
    ],
    
    "ac-drive-motor": [
        {
            "fault_code": "FC-TH-01",
            "fault_name": "Stator Winding Overtemperature — KTY84 Sensor",
            "description": "Stator winding temperature monitored by KTY84 sensor has exceeded alarm threshold, indicating cooling failure or overload.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 1.5,
                "bearing_temp_drive_end_c": 68,
                "stator_winding_temp_c": 138,
                "stator_phase_current_a": 24.1,
                "shaft_speed_rpm": 1795,
                "bearing_lube_oil_pressure_bar": 3.8
            },
            "thresholds": {
                "stator_winding_temp_c": {
                    "alarm": 130,
                    "trip": 145,
                    "citation": "Siemens 1PH7 IOM Section 2.5 — KTY84 temperature sensor in stator winding. Insulation Class F: alarm 130°C, trip 145°C"
                }
            },
            "risk_level": "HIGH",
            "probable_root_causes": [
                "Fan cover blocked reducing cooling airflow",
                "Converter overloading motor beyond rated duty",
                "KTY84 sensor circuit fault giving false high reading"
            ],
            "recommended_actions": [
                "Check fan cover and cooling air inlet openings for obstruction — Ref: Siemens 1PH7 IOM Section 2.5.1",
                "Verify converter output current does not exceed motor rated current — Ref: Siemens 1PH7 IOM Section 2.5.2",
                "Check KTY84 sensor resistance: at 130°C resistance ≈ 2200Ω — Ref: Siemens 1PH7 IOM Section 2.4 Rating Plate",
                "Reduce duty cycle if operating in intermittent load conditions",
                "Allow motor to cool to below 80°C before restart"
            ]
        }
    ],
    
    "synchronous-motor": [
        {
            "fault_code": "FC-TH-01",
            "fault_name": "Bearing Overtemperature — Sleeve Bearing",
            "description": "Sleeve bearing temperature has exceeded the alarm threshold. Synchronous motors with sleeve bearings require continuous oil film monitoring.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 2.2,
                "bearing_temp_drive_end_c": 108,
                "stator_winding_temp_c": 118,
                "stator_phase_current_a": 33.2,
                "shaft_speed_rpm": 1001,
                "bearing_lube_oil_pressure_bar": 2.1
            },
            "thresholds": {
                "bearing_temp_drive_end_c": {
                    "alarm": 100,
                    "trip": 110,
                    "citation": "WEG Synchronous Motor S Line IOM Section 6.3.5 — Sleeve bearing alarm temperature: 100°C, trip: 110°C. Motor must shut down immediately on trip."
                }
            },
            "risk_level": "CRITICAL",
            "probable_root_causes": [
                "Oil film breakdown in sleeve bearing due to low oil pressure",
                "Oil viscosity degradation — oil change interval exceeded",
                "Shaft misalignment causing uneven load on bearing surface"
            ],
            "recommended_actions": [
                "IMMEDIATE: Check oil level and oil pressure in sleeve bearing — Ref: WEG S Line IOM Section 6.3.5",
                "Verify oil pump is running and delivering correct pressure (min 2.5 bar) — Ref: WEG S Line IOM Section 6.2.1 Step 4",
                "Check oil temperature at bearing inlet — oil viscosity must be within specification",
                "Inspect sleeve bearing surfaces during next planned shutdown — Ref: WEG S Line IOM Section 7.12 Bearing Maintenance",
                "If temperature reaches 110°C — initiate emergency shutdown immediately — Ref: WEG S Line IOM Section 6.3.5"
            ]
        },
        {
            "fault_code": "FC-SY-01",
            "fault_name": "Loss of Synchronism",
            "description": "Motor has lost synchronism with power supply, causing field current oscillation and torque pulsations.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 4.2,
                "bearing_temp_drive_end_c": 88,
                "stator_winding_temp_c": 105,
                "stator_phase_current_a": 48.5,
                "shaft_speed_rpm": 965,
                "bearing_lube_oil_pressure_bar": 3.1
            },
            "thresholds": {
                "stator_phase_current_a": {
                    "alarm": "rated × 1.15",
                    "trip": "rated × 1.25",
                    "citation": "WEG S Line IOM Section 6.3.2 Resynchronization — On loss of synchronism, field current exceeds normal value. Disconnect field for 2–3 seconds to resynchronize."
                }
            },
            "risk_level": "CRITICAL",
            "probable_root_causes": [
                "Sudden load transient exceeding pull-out torque",
                "Excitation system fault causing field current loss",
                "Supply voltage dip causing loss of synchronism"
            ],
            "recommended_actions": [
                "Disconnect field power supply for 2–3 seconds to allow resynchronization — Ref: WEG S Line IOM Section 6.3.2",
                "Check excitation system voltage and current output",
                "Verify supply voltage at motor terminals — voltage dip may have caused pole slip",
                "Limit resynchronization attempts to maximum 2 — Ref: WEG S Line IOM Section 6.3.2 Step 4",
                "If motor fails to resynchronize after 2 attempts — shut down and investigate excitation system"
            ]
        }
    ],
    
    "heavy-duty-industrial-motor": [
        {
            "fault_code": "FC-TH-01",
            "fault_name": "Bearing Overtemperature — Sleeve Bearing Drive End",
            "description": "Sleeve bearing temperature on drive end has exceeded alarm threshold. Heavy-duty motors require forced lubrication monitoring.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 2.8,
                "bearing_temp_drive_end_c": 115,
                "stator_winding_temp_c": 128,
                "stator_phase_current_a": 39.8,
                "shaft_speed_rpm": 748,
                "bearing_lube_oil_pressure_bar": 1.2
            },
            "thresholds": {
                "bearing_temp_drive_end_c": {
                    "alarm": 110,
                    "trip": 120,
                    "citation": "WEG W60 IOM Section 7.8.3.6 Sleeve Bearing Operation — Alarm: 110°C, Trip: 120°C. Check oil circulation system immediately."
                },
                "bearing_lube_oil_pressure_bar": {
                    "alarm": 1.5,
                    "trip": 1.0,
                    "citation": "WEG W60 IOM Section 7.8.3.3 Cooling by Water Circulation and Section 6.2.1 Step 4 — Verify oil pressure and flow before startup"
                }
            },
            "risk_level": "CRITICAL",
            "probable_root_causes": [
                "Forced lubrication oil pump degraded output",
                "Oil filter blocked — high differential pressure across filter",
                "Bearing clearance increased due to wear — oil film instability"
            ],
            "recommended_actions": [
                "IMMEDIATE: Verify forced lubrication oil pump is running at rated pressure — Ref: WEG W60 IOM Section 6.2.1 Step 4",
                "Check oil filter differential pressure indicator — replace filter if blocked — Ref: WEG W60 IOM Section 7.8.3",
                "Inspect oil level in lubrication reservoir — minimum level must be maintained",
                "Check oil temperature at bearing inlet — viscosity must be within nameplate specification",
                "If bearing temp reaches 120°C — EMERGENCY SHUTDOWN — Ref: WEG W60 IOM Section 7.8.3.6",
                "After shutdown: disassemble bearing for inspection — Ref: WEG W60 IOM Section 7.8.3.8"
            ]
        },
        {
            "fault_code": "FC-VB-01",
            "fault_name": "High Shaft Vibration — Possible Bearing Wear",
            "description": "Shaft vibration exceeds Zone B limit indicating possible sleeve bearing wear or rotor imbalance in this heavy-duty application.",
            "sensor_spike": {
                "vibration_velocity_mm_s": 6.2,
                "bearing_temp_drive_end_c": 92,
                "stator_winding_temp_c": 105,
                "stator_phase_current_a": 38.1,
                "shaft_speed_rpm": 752,
                "bearing_lube_oil_pressure_bar": 3.8
            },
            "thresholds": {
                "vibration_velocity_mm_s": {
                    "alarm": 4.5,
                    "trip": 7.1,
                    "citation": "WEG W60 IOM Section 6.3.5 Vibration — Per ISO 10816-3 for motors >15kW on rigid mounting: Zone B limit 4.5 mm/s, Zone C limit 7.1 mm/s"
                }
            },
            "risk_level": "HIGH",
            "probable_root_causes": [
                "Sleeve bearing oil whirl instability",
                "Rotor bow due to thermal unbalance",
                "Foundation looseness causing resonance amplification"
            ],
            "recommended_actions": [
                "Perform vibration spectrum analysis — identify dominant frequency (oil whirl = 0.4–0.5× running speed) — Ref: WEG W60 IOM Section 6.3.5",
                "Check bearing oil clearance — excessive clearance causes oil whirl — Ref: WEG W60 IOM Section 7.8.3.6",
                "Inspect foundation anchor bolts for looseness — Ref: WEG W60 IOM Section 4.8.4",
                "Verify shaft alignment with driven machine — Ref: WEG W60 IOM Section 4.8.7",
                "Schedule bearing inspection at next planned maintenance window"
            ]
        }
    ]
}
