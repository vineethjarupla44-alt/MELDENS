import React, { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../common/GlassCard';
import { Button } from '../common/Button';
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import { 
  User, 
  HeartPulse, 
  Pill, 
  AlertCircle, 
  Plus, 
  Trash2, 
  Check,
  Calendar
} from 'lucide-react';
import type { 
  PatientIntakeSubmission, 
  ConditionIntakeItem, 
  AllergyIntakeItem, 
  MedicationIntakeItem 
} from '../../types';

interface PatientIntakeFormProps {
  initialData?: PatientIntakeSubmission;
  isEditing?: boolean;
  onSubmit: (data: PatientIntakeSubmission) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
}

export const PatientIntakeForm: React.FC<PatientIntakeFormProps> = ({
  initialData,
  isEditing = false,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const toDisplayDOB = (dateStr?: string): string => {
    if (!dateStr) return '';
    const trimmed = dateStr.trim();
    const yyyymmdd = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
    if (yyyymmdd) {
      return `${yyyymmdd[3]}-${yyyymmdd[2]}-${yyyymmdd[1]}`;
    }
    return trimmed;
  };

  // Demographics
  const [firstName, setFirstName] = useState(initialData?.first_name || '');
  const [lastName, setLastName] = useState(initialData?.last_name || '');
  const [dob, setDob] = useState(toDisplayDOB(initialData?.date_of_birth) || '');
  const [gender, setGender] = useState(initialData?.gender || 'Female');
  const [bloodType, setBloodType] = useState(initialData?.blood_type || '');
  const [calculatedAge, setCalculatedAge] = useState<number | null>(null);
  const dobInputRef = useRef<HTMLInputElement>(null);

  const normalizeDateToISO = (dateStr: string): string => {
    if (!dateStr) return '';
    const trimmed = dateStr.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      return trimmed;
    }
    // Match DD-MM-YYYY or DD/MM/YYYY
    const ddmmyyyy = /^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/.exec(trimmed);
    if (ddmmyyyy) {
      const day = ddmmyyyy[1].padStart(2, '0');
      const month = ddmmyyyy[2].padStart(2, '0');
      const year = ddmmyyyy[3];
      return `${year}-${month}-${day}`;
    }
    return trimmed;
  };

  // Clinical Fields
  const [symptoms, setSymptoms] = useState(initialData?.symptoms || '');
  const [conditions, setConditions] = useState<ConditionIntakeItem[]>(
    initialData?.existing_conditions || []
  );
  const [allergies, setAllergies] = useState<AllergyIntakeItem[]>(
    initialData?.allergies || []
  );
  const [medications, setMedications] = useState<MedicationIntakeItem[]>(
    initialData?.current_medications || []
  );
  const [additionalNotes, setAdditionalNotes] = useState(initialData?.additional_notes || '');
  const [emergencyName, setEmergencyName] = useState(initialData?.emergency_contact_name || '');
  const [emergencyPhone, setEmergencyPhone] = useState(initialData?.emergency_contact_phone || '');

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Synchronize state when initialData changes
  useEffect(() => {
    if (initialData) {
      setFirstName(initialData.first_name || '');
      setLastName(initialData.last_name || '');
      setDob(toDisplayDOB(initialData.date_of_birth) || '');
      setGender(initialData.gender || 'Female');
      setBloodType(initialData.blood_type || '');
      setSymptoms(initialData.symptoms || '');
      setConditions(initialData.existing_conditions || []);
      setAllergies(initialData.allergies || []);
      setMedications(initialData.current_medications || []);
      setAdditionalNotes(initialData.additional_notes || '');
      setEmergencyName(initialData.emergency_contact_name || '');
      setEmergencyPhone(initialData.emergency_contact_phone || '');
    }
  }, [initialData]);

  // Auto-calculate age whenever DOB changes (safe timezone-free split, supports DD-MM-YYYY and YYYY-MM-DD)
  useEffect(() => {
    const iso = normalizeDateToISO(dob);
    if (iso && /^\d{4}-\d{2}-\d{2}$/.test(iso)) {
      const [year, month, day] = iso.split('-').map(Number);
      const birth = new Date(year, month - 1, day);
      const now = new Date();
      let age = now.getFullYear() - birth.getFullYear();
      const m = now.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
        age--;
      }
      setCalculatedAge(age >= 0 ? age : null);
    } else {
      setCalculatedAge(null);
    }
  }, [dob]);

  // Helpers to add items
  const addCondition = () => {
    setConditions([...conditions, { condition_name: '', onset_date: '', clinical_status: 'ACTIVE' }]);
  };
  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const addAllergy = () => {
    setAllergies([...allergies, { allergen: '', reaction: '', severity: 'MODERATE' }]);
  };
  const removeAllergy = (index: number) => {
    setAllergies(allergies.filter((_, i) => i !== index));
  };

  const addMedication = () => {
    setMedications([...medications, { medication_name: '', dosage: '', frequency: '', route: 'Oral' }]);
  };
  const removeMedication = (index: number) => {
    setMedications(medications.filter((_, i) => i !== index));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!firstName.trim()) newErrors.firstName = 'First name is required';
    if (!lastName.trim()) newErrors.lastName = 'Last name is required';
    const iso = normalizeDateToISO(dob);
    if (!dob.trim()) {
      newErrors.dob = 'Date of birth is required';
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
      newErrors.dob = 'Please enter valid date of birth (DD-MM-YYYY or YYYY-MM-DD)';
    } else {
      const [year, month, day] = iso.split('-').map(Number);
      const birth = new Date(year, month - 1, day);
      const now = new Date();
      if (birth > now) {
        newErrors.dob = 'Date of birth cannot be in the future';
      } else if (year < 1900) {
        newErrors.dob = 'Please enter a valid birth year (1900 or later)';
      }
    }


    // Validate any populated condition has a name
    conditions.forEach((c, idx) => {
      if (!c.condition_name.trim()) {
        newErrors[`cond_${idx}`] = 'Condition name cannot be empty';
      }
    });

    // Validate any populated allergy has an allergen
    allergies.forEach((a, idx) => {
      if (!a.allergen.trim()) {
        newErrors[`all_${idx}`] = 'Allergen cannot be empty';
      }
    });

    // Validate any medication has a name
    medications.forEach((m, idx) => {
      if (!m.medication_name.trim()) {
        newErrors[`med_${idx}`] = 'Medication name cannot be empty';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const payload: PatientIntakeSubmission = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      date_of_birth: normalizeDateToISO(dob),
      gender,
      blood_type: bloodType.trim() || undefined,
      symptoms: symptoms.trim() || undefined,
      existing_conditions: conditions.filter(c => c.condition_name.trim()),
      allergies: allergies.filter(a => a.allergen.trim()),
      current_medications: medications.filter(m => m.medication_name.trim()),
      additional_notes: additionalNotes.trim() || undefined,
      emergency_contact_name: emergencyName.trim() || undefined,
      emergency_contact_phone: emergencyPhone.trim() || undefined,
      preferred_language: 'English',
    };

    await onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header Banner with Provenance Tag */}
      <GlassCard variant="glow" className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl font-bold text-white">
              {isEditing ? 'Edit Patient Intake Form' : 'Clinical Patient Intake Form'}
            </h2>
            <ProvenanceBadge source="PATIENT_INPUT" />
          </div>
          <p className="text-xs text-slate-400">
            Information entered here is registered strictly as <strong className="text-cyan-400">PATIENT_INPUT</strong>. 
            AI algorithms are forbidden from altering or modifying these facts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onCancel && (
            <Button type="button" variant="secondary" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" variant="primary" size="sm" isLoading={isLoading}>
            <Check className="w-4 h-4 mr-1.5" />
            {isEditing ? 'Save Changes' : 'Submit Intake Record'}
          </Button>
        </div>
      </GlassCard>

      {/* Section 1: Demographics */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
            <User className="w-4 h-4" />
            <h3>Patient Demographics</h3>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Required Identification</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              First Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="e.g. Arthur"
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            />
            {errors.firstName && <p className="text-xs text-rose-400 mt-1">{errors.firstName}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Last Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="e.g. Dent"
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            />
            {errors.lastName && <p className="text-xs text-rose-400 mt-1">{errors.lastName}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Date of Birth <span className="text-rose-400">*</span>
              <span className="text-[10px] text-cyan-400 font-mono ml-1.5">(Format: DD-MM-YYYY)</span>
            </label>
            <div className="relative flex items-center">
              <input
                type="text"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                placeholder="DD-MM-YYYY (e.g. 12-04-1968)"
                maxLength={10}
                className="w-full px-3 py-2 pr-10 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white font-mono placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
              />
              <input
                ref={dobInputRef}
                type="date"
                max={new Date().toISOString().split('T')[0]}
                tabIndex={-1}
                className="sr-only"
                onChange={(e) => {
                  if (e.target.value) {
                    const [y, m, d] = e.target.value.split('-');
                    setDob(`${d}-${m}-${y}`);
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  try {
                    dobInputRef.current?.showPicker?.();
                  } catch {
                    dobInputRef.current?.click();
                  }
                }}
                className="absolute right-2 text-slate-400 hover:text-cyan-400 transition-colors p-1 cursor-pointer"
                title="Select date from calendar"
              >
                <Calendar className="w-4 h-4 text-cyan-400" />
              </button>
            </div>
            {calculatedAge !== null ? (
              <span className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <Check className="w-3 h-3" /> Valid DOB — Calculated Age: {calculatedAge} years
              </span>
            ) : dob.trim().length > 0 ? (
              <span className="text-[11px] text-amber-400/90 mt-1 block font-mono">
                Format: DD-MM-YYYY (e.g. 15-08-1980)
              </span>
            ) : null}
            {errors.dob && <p className="text-xs text-rose-400 mt-1">{errors.dob}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Biological Sex / Gender
            </label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            >
              <option value="Female">Female</option>
              <option value="Male">Male</option>
              <option value="Other">Other</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Blood Type (Optional)
            </label>
            <select
              value={bloodType}
              onChange={(e) => setBloodType(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            >
              <option value="">Unknown / Not Tested</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Section 2: Symptoms & Chief Complaints */}
      <GlassCard className="space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
            <HeartPulse className="w-4 h-4" />
            <h3>Chief Complaints & Present Symptoms</h3>
          </div>
          <span className="text-[11px] text-amber-400/80 bg-amber-950/40 border border-amber-500/20 px-2 py-0.5 rounded">
            Patient Reported
          </span>
        </div>
        <textarea
          rows={3}
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="Describe your current symptoms, onset, and severity (e.g. Mild shortness of breath when walking uphill, occasional dry cough in mornings)..."
          className="w-full px-3 py-2.5 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 leading-relaxed"
        />
      </GlassCard>

      {/* Section 3: Current Medications */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-purple-400 font-semibold text-sm">
            <Pill className="w-4 h-4" />
            <h3>Current Medications</h3>
          </div>
          <Button type="button" variant="secondary" size="sm" onClick={addMedication}>
            <Plus className="w-3.5 h-3.5 mr-1" /> Add Medication
          </Button>
        </div>

        {medications.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No current medications added.</p>
        ) : (
          <div className="space-y-3">
            {medications.map((med, index) => (
              <div key={index} className="grid grid-cols-1 sm:grid-cols-4 gap-2 bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 items-end">
                <div className="sm:col-span-1">
                  <label className="block text-[11px] text-slate-400 mb-0.5">Medication Name</label>
                  <input
                    type="text"
                    value={med.medication_name}
                    onChange={(e) => {
                      const updated = [...medications];
                      updated[index].medication_name = e.target.value;
                      setMedications(updated);
                    }}
                    placeholder="e.g. Metformin"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                  {errors[`med_${index}`] && (
                    <p className="text-[10px] text-rose-400 mt-0.5">{errors[`med_${index}`]}</p>
                  )}
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-0.5">Dosage</label>
                  <input
                    type="text"
                    value={med.dosage || ''}
                    onChange={(e) => {
                      const updated = [...medications];
                      updated[index].dosage = e.target.value;
                      setMedications(updated);
                    }}
                    placeholder="e.g. 500 mg"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-0.5">Frequency</label>
                  <input
                    type="text"
                    value={med.frequency || ''}
                    onChange={(e) => {
                      const updated = [...medications];
                      updated[index].frequency = e.target.value;
                      setMedications(updated);
                    }}
                    placeholder="e.g. Once daily"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="flex items-center justify-end">
                  <Button 
                    type="button" 
                    variant="danger" 
                    size="sm" 
                    onClick={() => removeMedication(index)}
                    className="px-2 py-1 text-xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Section 4: Known Allergies */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
            <AlertCircle className="w-4 h-4" />
            <h3>Known Drug & Environmental Allergies</h3>
          </div>
          <Button type="button" variant="secondary" size="sm" onClick={addAllergy}>
            <Plus className="w-3.5 h-3.5 mr-1" /> Add Allergy
          </Button>
        </div>

        {allergies.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No known allergies entered.</p>
        ) : (
          <div className="space-y-3">
            {allergies.map((al, index) => (
              <div key={index} className="grid grid-cols-1 sm:grid-cols-4 gap-2 bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 items-end">
                <div className="sm:col-span-1">
                  <label className="block text-[11px] text-slate-400 mb-0.5">Allergen</label>
                  <input
                    type="text"
                    value={al.allergen}
                    onChange={(e) => {
                      const updated = [...allergies];
                      updated[index].allergen = e.target.value;
                      setAllergies(updated);
                    }}
                    placeholder="e.g. Penicillin"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                  {errors[`all_${index}`] && (
                    <p className="text-[10px] text-rose-400 mt-0.5">{errors[`all_${index}`]}</p>
                  )}
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-0.5">Observed Reaction</label>
                  <input
                    type="text"
                    value={al.reaction || ''}
                    onChange={(e) => {
                      const updated = [...allergies];
                      updated[index].reaction = e.target.value;
                      setAllergies(updated);
                    }}
                    placeholder="e.g. Hives, facial swelling"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-0.5">Severity</label>
                  <select
                    value={al.severity}
                    onChange={(e: any) => {
                      const updated = [...allergies];
                      updated[index].severity = e.target.value;
                      setAllergies(updated);
                    }}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="MILD">Mild</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="SEVERE">Severe / Anaphylaxis</option>
                  </select>
                </div>
                <div className="flex items-center justify-end">
                  <Button 
                    type="button" 
                    variant="danger" 
                    size="sm" 
                    onClick={() => removeAllergy(index)}
                    className="px-2 py-1 text-xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Section 5: Existing Medical Conditions */}
      <GlassCard className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
            <HeartPulse className="w-4 h-4" />
            <h3>Existing Medical Conditions</h3>
          </div>
          <Button type="button" variant="secondary" size="sm" onClick={addCondition}>
            <Plus className="w-3.5 h-3.5 mr-1" /> Add Condition
          </Button>
        </div>

        {conditions.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No existing medical conditions listed.</p>
        ) : (
          <div className="space-y-3">
            {conditions.map((cond, index) => (
              <div key={index} className="grid grid-cols-1 sm:grid-cols-4 gap-2 bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 items-end">
                <div className="sm:col-span-2">
                  <label className="block text-[11px] text-slate-400 mb-0.5">Condition Name</label>
                  <input
                    type="text"
                    value={cond.condition_name}
                    onChange={(e) => {
                      const updated = [...conditions];
                      updated[index].condition_name = e.target.value;
                      setConditions(updated);
                    }}
                    placeholder="e.g. Type 2 Diabetes"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                  {errors[`cond_${index}`] && (
                    <p className="text-[10px] text-rose-400 mt-0.5">{errors[`cond_${index}`]}</p>
                  )}
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-0.5">Onset Year / Date</label>
                  <input
                    type="text"
                    value={cond.onset_date || ''}
                    onChange={(e) => {
                      const updated = [...conditions];
                      updated[index].onset_date = e.target.value;
                      setConditions(updated);
                    }}
                    placeholder="e.g. 2020"
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div className="flex items-center justify-end">
                  <Button 
                    type="button" 
                    variant="danger" 
                    size="sm" 
                    onClick={() => removeCondition(index)}
                    className="px-2 py-1 text-xs"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Section 6: Additional Notes & Emergency Contact */}
      <GlassCard className="space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-slate-200">Additional Notes & Emergency Contact</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Emergency Contact Name
            </label>
            <input
              type="text"
              value={emergencyName}
              onChange={(e) => setEmergencyName(e.target.value)}
              placeholder="e.g. Thomas Vance"
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Emergency Contact Phone
            </label>
            <input
              type="tel"
              value={emergencyPhone}
              onChange={(e) => setEmergencyPhone(e.target.value)}
              placeholder="e.g. +1 (555) 019-2834"
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Additional Health Notes or Comments
            </label>
            <textarea
              rows={2}
              value={additionalNotes}
              onChange={(e) => setAdditionalNotes(e.target.value)}
              placeholder="Any surgical history, dietary restrictions, or care preferences..."
              className="w-full px-3 py-2 text-sm bg-slate-950/80 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </GlassCard>

      {/* Submission Actions */}
      <div className="flex items-center justify-end gap-3 pt-2">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" variant="primary" isLoading={isLoading}>
          <Check className="w-4 h-4 mr-1.5" />
          {isEditing ? 'Save Changes' : 'Submit Patient Intake Record'}
        </Button>
      </div>
    </form>
  );
};
