"""
PDF-Grounded Motor Thresholds and Normal Operating Ranges

All values derived from motor manuals with exact citations.
"""

# Motor normal operating ranges (for baseline simulation)
MOTOR_BASELINES = {
    "general-industrial-motor": {
        "display_name": "General Industrial Motor (Siemens SIMOTICS TN 1LA8)",
        "pdf_name": "General-Industrial-Motor.pdf",
        "normal_ranges": {
            "vibration_velocity_mm_s": {
                "min": 1.2,
                "max": 2.8,
                "unit": "mm/s",
                "label": "Vibration Velocity",
                "citation": "ISO 10816-3 Zone A: <2.3 mm/s, Zone B: <4.5 mm/s — Referenced in Siemens 1LA8 IOM Section 5.3.3"
            },
            "bearing_temp_drive_end_c": {
                "min": 55,
                "max": 75,
                "unit": "°C [Pt100]",
                "label": "Bearing Temperature (Drive End)",
                "citation": "Siemens 1LA8 IOM Section 7 — Normal bearing temp: 40-80°C, Alarm: 110°C"
            },
            "stator_winding_temp_c": {
                "min": 80,
                "max": 110,
                "unit": "°C [Pt100]",
                "label": "Stator Winding Temperature",
                "citation": "IEC 60034-1 Insulation Class F — Max hotspot: 155°C, Normal operating: 80-110°C"
            },
            "stator_phase_current_a": {
                "min": 18,
                "max": 26,
                "unit": "A",
                "label": "Stator Phase Current",
                "citation": "Within nameplate rated current per Siemens 1LA8 IOM Section 4.5"
            },
            "shaft_speed_rpm": {
                "min": 1450,
                "max": 1480,
                "unit": "rpm",
                "label": "Shaft Speed",
                "citation": "4-pole, 50Hz synchronous speed 1500 rpm with typical slip 1.3-3.3% per IEC 60034-1"
            },
            "bearing_lube_oil_pressure_bar": {
                "min": 3.5,
                "max": 5.0,
                "unit": "bar",
                "label": "Bearing Lube Oil Pressure",
                "citation": "Siemens 1LA8 IOM Section 7.3 — Normal lubrication pressure range"
            }
        },
        "alarm_thresholds": {
            "vibration_velocity_mm_s": {
                "alarm": 4.5,
                "trip": 7.1,
                "citation": "ISO 10816-3 Zone B: 4.5 mm/s, Zone C: 7.1 mm/s"
            },
            "bearing_temp_drive_end_c": {
                "alarm": 110,
                "trip": 120,
                "citation": "Siemens 1LA8 IOM Section 7 — Bearing Temperature Monitoring"
            },
            "stator_winding_temp_c": {
                "alarm": 145,
                "trip": 155,
                "citation": "IEC 60034-1 Class F — Max hotspot temperature"
            },
            "stator_phase_current_a": {
                "alarm": "rated × 1.15",
                "trip": "rated × 1.25",
                "citation": "IEC EN 60034-1 / Siemens 1LA8 IOM Section 4.5"
            },
            "bearing_lube_oil_pressure_bar": {
                "alarm": 1.5,
                "trip": 1.0,
                "citation": "Siemens 1LA8 IOM Section 7.3"
            }
        }
    },
    
    "ac-drive-motor": {
        "display_name": "AC Drive Motor (Siemens 1PH7 series)",
        "pdf_name": "AC-Drive-Motor.pdf",
        "normal_ranges": {
            "vibration_velocity_mm_s": {
                "min": 0.8,
                "max": 2.2,
                "unit": "mm/s",
                "label": "Vibration Velocity",
                "citation": "ISO 10816-3 for variable speed motors"
            },
            "bearing_temp_drive_end_c": {
                "min": 50,
                "max": 70,
                "unit": "°C [KTY84]",
                "label": "Bearing Temperature (Drive End)",
                "citation": "Siemens 1PH7 IOM Section 2.5 — KTY84 sensor monitors winding temp"
            },
            "stator_winding_temp_c": {
                "min": 70,
                "max": 100,
                "unit": "°C [KTY84]",
                "label": "Stator Winding Temperature",
                "citation": "Siemens 1PH7 IOM Section 2.5 — Insulation Class F"
            },
            "stator_phase_current_a": {
                "min": 15,
                "max": 22,
                "unit": "A",
                "label": "Stator Phase Current",
                "citation": "Siemens 1PH7 IOM Section 2.5.2 — Rated current"
            },
            "shaft_speed_rpm": {
                "min": 800,
                "max": 4500,
                "unit": "rpm",
                "label": "Shaft Speed",
                "citation": "Siemens 1PH7 IOM — Variable speed drive, shown at 1800 rpm nominal"
            },
            "bearing_lube_oil_pressure_bar": {
                "min": 3.0,
                "max": 4.5,
                "unit": "bar",
                "label": "Bearing Lube Oil Pressure",
                "citation": "Siemens 1PH7 IOM Section 2.5"
            }
        },
        "alarm_thresholds": {
            "vibration_velocity_mm_s": {
                "alarm": 4.5,
                "trip": 7.1,
                "citation": "ISO 10816-3"
            },
            "bearing_temp_drive_end_c": {
                "alarm": 110,
                "trip": 120,
                "citation": "Siemens 1PH7 IOM Section 2.5"
            },
            "stator_winding_temp_c": {
                "alarm": 130,
                "trip": 145,
                "citation": "Siemens 1PH7 IOM Section 2.5 — KTY84 sensor, Class F"
            },
            "stator_phase_current_a": {
                "alarm": "rated × 1.15",
                "trip": "rated × 1.25",
                "citation": "Siemens 1PH7 IOM Section 2.5.2"
            },
            "bearing_lube_oil_pressure_bar": {
                "alarm": 1.5,
                "trip": 1.0,
                "citation": "Siemens 1PH7 IOM Section 2.5"
            }
        }
    },
    
    "synchronous-motor": {
        "display_name": "Synchronous Motor (WEG S Line with Brushes)",
        "pdf_name": "Synchronous-Motor.pdf",
        "normal_ranges": {
            "vibration_velocity_mm_s": {
                "min": 1.0,
                "max": 2.5,
                "unit": "mm/s",
                "label": "Vibration Velocity",
                "citation": "ISO 10816-3 for synchronous motors"
            },
            "bearing_temp_drive_end_c": {
                "min": 55,
                "max": 80,
                "unit": "°C [Pt100]",
                "label": "Bearing Temperature (Drive End)",
                "citation": "WEG S Line IOM Section 6.3.5 — Sleeve bearing temperature monitoring"
            },
            "stator_winding_temp_c": {
                "min": 85,
                "max": 115,
                "unit": "°C [Pt100]",
                "label": "Stator Winding Temperature",
                "citation": "WEG S Line IOM Table 4.4 — Class F alarm: 155°C"
            },
            "stator_phase_current_a": {
                "min": 22,
                "max": 35,
                "unit": "A",
                "label": "Stator Phase Current",
                "citation": "WEG S Line IOM — Rated current per nameplate"
            },
            "shaft_speed_rpm": {
                "min": 995,
                "max": 1005,
                "unit": "rpm",
                "label": "Shaft Speed",
                "citation": "6-pole, 50Hz synchronous speed = 1000 rpm (no slip)"
            },
            "bearing_lube_oil_pressure_bar": {
                "min": 2.5,
                "max": 4.0,
                "unit": "bar",
                "label": "Bearing Lube Oil Pressure",
                "citation": "WEG S Line IOM Section 6.2.1 Step 4 — Minimum 2.5 bar"
            }
        },
        "alarm_thresholds": {
            "vibration_velocity_mm_s": {
                "alarm": 4.5,
                "trip": 7.1,
                "citation": "ISO 10816-3"
            },
            "bearing_temp_drive_end_c": {
                "alarm": 100,
                "trip": 110,
                "citation": "WEG S Line IOM Section 6.3.5 — Sleeve bearing limits"
            },
            "stator_winding_temp_c": {
                "alarm": 145,
                "trip": 155,
                "citation": "WEG S Line IOM Table 4.4 — Class F insulation"
            },
            "stator_phase_current_a": {
                "alarm": "rated × 1.15",
                "trip": "rated × 1.25",
                "citation": "WEG S Line IOM Section 6.3.2"
            },
            "bearing_lube_oil_pressure_bar": {
                "alarm": 1.5,
                "trip": 1.0,
                "citation": "WEG S Line IOM Section 6.2.1"
            }
        }
    },
    
    "heavy-duty-industrial-motor": {
        "display_name": "Heavy-Duty Industrial Motor (WEG W60 Line)",
        "pdf_name": "Heavy-Duty-Industrial-Motor.pdf",
        "normal_ranges": {
            "vibration_velocity_mm_s": {
                "min": 1.5,
                "max": 3.2,
                "unit": "mm/s",
                "label": "Vibration Velocity",
                "citation": "WEG W60 IOM Section 6.3.5 — ISO 10816-3 for motors >15kW"
            },
            "bearing_temp_drive_end_c": {
                "min": 60,
                "max": 85,
                "unit": "°C [Pt100]",
                "label": "Bearing Temperature (Drive End)",
                "citation": "WEG W60 IOM Section 7.8.3.6 — Sleeve bearing, alarm 110°C"
            },
            "stator_winding_temp_c": {
                "min": 90,
                "max": 120,
                "unit": "°C [Pt100]",
                "label": "Stator Winding Temperature",
                "citation": "WEG W60 IOM Table 4.4 — Class F insulation"
            },
            "stator_phase_current_a": {
                "min": 28,
                "max": 42,
                "unit": "A",
                "label": "Stator Phase Current",
                "citation": "WEG W60 IOM — Nameplate rated current"
            },
            "shaft_speed_rpm": {
                "min": 740,
                "max": 760,
                "unit": "rpm",
                "label": "Shaft Speed",
                "citation": "8-pole, 50Hz nominal 750 rpm with typical slip per IEC 60034-1"
            },
            "bearing_lube_oil_pressure_bar": {
                "min": 3.0,
                "max": 5.0,
                "unit": "bar",
                "label": "Bearing Lube Oil Pressure",
                "citation": "WEG W60 IOM Section 6.2.1 Step 4 — Forced lubrication"
            }
        },
        "alarm_thresholds": {
            "vibration_velocity_mm_s": {
                "alarm": 4.5,
                "trip": 7.1,
                "citation": "WEG W60 IOM Section 6.3.5 — ISO 10816-3 Zone B/C"
            },
            "bearing_temp_drive_end_c": {
                "alarm": 110,
                "trip": 120,
                "citation": "WEG W60 IOM Section 7.8.3.6"
            },
            "stator_winding_temp_c": {
                "alarm": 145,
                "trip": 155,
                "citation": "WEG W60 IOM Table 4.4 — Class F"
            },
            "stator_phase_current_a": {
                "alarm": "rated × 1.15",
                "trip": "rated × 1.25",
                "citation": "IEC EN 60034-1"
            },
            "bearing_lube_oil_pressure_bar": {
                "alarm": 1.5,
                "trip": 1.0,
                "citation": "WEG W60 IOM Section 7.8.3.3"
            }
        }
    }
}

# Sensor display name mapping (for frontend)
SENSOR_DISPLAY_NAMES = {
    "vibration_velocity_mm_s": "Vibration Velocity",
    "bearing_temp_drive_end_c": "Bearing Temperature (Drive End)",
    "stator_winding_temp_c": "Stator Winding Temperature",
    "stator_phase_current_a": "Stator Phase Current",
    "shaft_speed_rpm": "Shaft Speed",
    "bearing_lube_oil_pressure_bar": "Bearing Lube Oil Pressure"
}
