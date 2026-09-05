import React, { useState, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Float } from '@react-three/drei';
import * as THREE from 'three';
import { 
  RotateCcw, 
  ShieldCheck, 
  Layers
} from 'lucide-react';

export interface GraphNodeData {
  id: string;
  label: string;
  category: string;
  count?: number | string;
  description: string;
  position: [number, number, number];
  color: string;
  iconName: string;
}

interface ClinicalGraph3DProps {
  patientName?: string;
  patientMrn?: string;
  counts?: {
    documents?: number;
    labs?: number;
    medications?: number;
    conditions?: number;
    allergies?: number;
    timeline?: number;
    conflicts?: number;
    summary?: number | string;
  };
  onSelectNode?: (nodeId: string) => void;
  height?: string;
}

// Interactive Single Node Component
const GraphNode: React.FC<{
  node: GraphNodeData;
  isHovered: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
  onDoubleClick: (pos: [number, number, number]) => void;
}> = ({ node, isHovered, onHover, onClick, onDoubleClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.4;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z -= delta * 0.25;
      ringRef.current.rotation.x += delta * 0.15;
    }
  });

  const baseScale = isHovered ? 1.3 : 1.0;

  return (
    <group position={node.position}>
      {/* Halo / Selection Ring */}
      <mesh ref={ringRef} scale={baseScale * 1.5}>
        <ringGeometry args={[0.7, 0.75, 32]} />
        <meshBasicMaterial 
          color={node.color} 
          transparent 
          opacity={isHovered ? 0.7 : 0.25} 
          side={THREE.DoubleSide} 
        />
      </mesh>

      {/* Main Node Sphere */}
      <mesh
        ref={meshRef}
        scale={baseScale}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover(node.id);
        }}
        onPointerOut={() => onHover(null)}
        onClick={(e) => {
          e.stopPropagation();
          onClick(node.id);
        }}
        onDoubleClick={(e) => {
          e.stopPropagation();
          onDoubleClick(node.position);
        }}
      >
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshStandardMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={isHovered ? 0.8 : 0.3}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>

      {/* HTML Label & Tooltip */}
      <Html
        distanceFactor={18}
        position={[0, -0.9, 0]}
        center
        className="pointer-events-none select-none transition-all duration-200"
      >
        <div
          className={`flex flex-col items-center transition-all ${
            isHovered ? 'scale-110 z-50' : 'scale-95 opacity-80'
          }`}
        >
          <div
            className="px-2.5 py-1 rounded-md border text-[11px] font-mono font-bold whitespace-nowrap shadow-lg backdrop-blur-md transition-all flex items-center gap-1.5"
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.85)',
              borderColor: isHovered ? node.color : 'rgba(71, 85, 105, 0.5)',
              color: isHovered ? '#ffffff' : '#cbd5e1',
              boxShadow: isHovered ? `0 0 12px ${node.color}66` : 'none',
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: node.color }}
            />
            <span>{node.label}</span>
            {node.count !== undefined && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800/80 text-slate-300">
                {node.count}
              </span>
            )}
          </div>

          {/* Expanded Tooltip on Hover */}
          {isHovered && (
            <div className="mt-1.5 p-2 rounded-lg bg-slate-950/95 border border-cyan-500/40 text-[11px] text-slate-300 max-w-[210px] shadow-2xl backdrop-blur-md text-center pointer-events-auto animate-fadeIn">
              <p className="font-semibold text-white mb-0.5">{node.label}</p>
              <p className="text-[10px] text-slate-400 leading-tight mb-1.5">
                {node.description}
              </p>
              <span className="inline-block text-[9px] font-mono text-cyan-400 bg-cyan-950/70 border border-cyan-500/30 px-2 py-0.5 rounded">
                Click to view records
              </span>
            </div>
          )}
        </div>
      </Html>
    </group>
  );
};

// Patient Core Component (Center)
const PatientCore: React.FC<{
  patientName: string;
  patientMrn: string;
  isHovered: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}> = ({ patientName, patientMrn, isHovered, onHover, onClick }) => {
  const coreRef = useRef<THREE.Mesh>(null);
  const outerRing1 = useRef<THREE.Mesh>(null);
  const outerRing2 = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (coreRef.current) {
      coreRef.current.rotation.y += delta * 0.3;
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.04;
      coreRef.current.scale.set(pulse, pulse, pulse);
    }
    if (outerRing1.current) {
      outerRing1.current.rotation.x += delta * 0.2;
      outerRing1.current.rotation.y += delta * 0.15;
    }
    if (outerRing2.current) {
      outerRing2.current.rotation.y -= delta * 0.25;
      outerRing2.current.rotation.z += delta * 0.15;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Orbital Outer Rings */}
      <mesh ref={outerRing1}>
        <torusGeometry args={[1.8, 0.02, 16, 64]} />
        <meshBasicMaterial color="#06b6d4" transparent opacity={0.3} />
      </mesh>
      <mesh ref={outerRing2}>
        <torusGeometry args={[2.2, 0.02, 16, 64]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.2} />
      </mesh>

      {/* Central Patient Core Sphere */}
      <mesh
        ref={coreRef}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover('core');
        }}
        onPointerOut={() => onHover(null)}
        onClick={(e) => {
          e.stopPropagation();
          onClick('patient-info');
        }}
      >
        <sphereGeometry args={[1.0, 36, 36]} />
        <meshStandardMaterial
          color="#0891b2"
          emissive="#06b6d4"
          emissiveIntensity={isHovered ? 0.9 : 0.45}
          roughness={0.15}
          metalness={0.8}
        />
      </mesh>

      {/* Center Label */}
      <Html distanceFactor={18} position={[0, -1.5, 0]} center className="pointer-events-none select-none">
        <div className="flex flex-col items-center">
          <div className="px-3 py-1 rounded-full border border-cyan-500/50 bg-slate-950/90 text-xs font-mono font-bold text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.4)] backdrop-blur-md whitespace-nowrap">
            PATIENT CORE
          </div>
          <span className="text-[10px] text-slate-400 font-mono mt-0.5">
            {patientName} ({patientMrn})
          </span>
        </div>
      </Html>
    </group>
  );
};

// Line Connector Component
const RelationshipLine: React.FC<{
  start: [number, number, number];
  end: [number, number, number];
  color?: string;
  opacity?: number;
}> = ({ start, end, color = '#0891b2', opacity = 0.25 }) => {
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end]);
  const lineGeo = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);

  return (
    <primitive object={new THREE.Line(
      lineGeo,
      new THREE.LineBasicMaterial({
        color: new THREE.Color(color),
        transparent: true,
        opacity: opacity,
        linewidth: 1,
      })
    )} />
  );
};

// Scene Wrapper
const Scene: React.FC<{
  nodes: GraphNodeData[];
  patientName: string;
  patientMrn: string;
  hoveredId: string | null;
  onHover: (id: string | null) => void;
  onSelect: (id: string) => void;
  controlsRef: React.RefObject<any>;
}> = ({ nodes, patientName, patientMrn, hoveredId, onHover, onSelect, controlsRef }) => {
  const handleDoubleClick = (pos: [number, number, number]) => {
    if (controlsRef.current) {
      controlsRef.current.target.set(pos[0], pos[1], pos[2]);
    }
  };

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 15, 10]} intensity={1.2} color="#38bdf8" />
      <pointLight position={[-10, -10, -10]} intensity={0.7} color="#06b6d4" />

      {/* Central Core */}
      <PatientCore
        patientName={patientName}
        patientMrn={patientMrn}
        isHovered={hoveredId === 'core'}
        onHover={onHover}
        onClick={onSelect}
      />

      {/* Orbiting Nodes */}
      <Float speed={1.2} rotationIntensity={0.2} floatIntensity={0.4}>
        {nodes.map((node) => (
          <GraphNode
            key={node.id}
            node={node}
            isHovered={hoveredId === node.id}
            onHover={onHover}
            onClick={onSelect}
            onDoubleClick={handleDoubleClick}
          />
        ))}
      </Float>

      {/* Relationship Lines to Central Core */}
      {nodes.map((node) => (
        <RelationshipLine
          key={`line-core-${node.id}`}
          start={[0, 0, 0]}
          end={node.position}
          color={hoveredId === node.id ? node.color : '#0e7490'}
          opacity={hoveredId === node.id ? 0.75 : 0.22}
        />
      ))}

      {/* Inter-node Relationship Lines (Cross-connections) */}
      <RelationshipLine
        start={nodes.find((n) => n.id === 'documents')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'labs')?.position || [0, 0, 0]}
        color="#10b981"
        opacity={0.2}
      />
      <RelationshipLine
        start={nodes.find((n) => n.id === 'documents')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'medications')?.position || [0, 0, 0]}
        color="#a855f7"
        opacity={0.2}
      />
      <RelationshipLine
        start={nodes.find((n) => n.id === 'labs')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'conflicts')?.position || [0, 0, 0]}
        color="#ef4444"
        opacity={0.25}
      />
      <RelationshipLine
        start={nodes.find((n) => n.id === 'medications')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'conflicts')?.position || [0, 0, 0]}
        color="#ef4444"
        opacity={0.25}
      />
      <RelationshipLine
        start={nodes.find((n) => n.id === 'labs')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'timeline')?.position || [0, 0, 0]}
        color="#14b8a6"
        opacity={0.2}
      />
      <RelationshipLine
        start={nodes.find((n) => n.id === 'ai-summary')?.position || [0, 0, 0]}
        end={nodes.find((n) => n.id === 'labs')?.position || [0, 0, 0]}
        color="#8b5cf6"
        opacity={0.2}
      />

      <OrbitControls
        ref={controlsRef}
        enablePan={false}
        enableZoom={true}
        minDistance={6}
        maxDistance={24}
        autoRotate={true}
        autoRotateSpeed={0.5}
        dampingFactor={0.05}
      />
    </>
  );
};

export const ClinicalGraph3D: React.FC<ClinicalGraph3DProps> = ({
  patientName = 'Eleanor Vance',
  patientMrn = 'MED-SYNTH-8492',
  counts = {},
  onSelectNode,
  height = '500px',
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const controlsRef = useRef<any>(null);

  // Position nodes in a 3D orbital circle around center
  const nodes: GraphNodeData[] = useMemo(() => {
    const rawNodes = [
      {
        id: 'patient-info',
        label: 'Patient Profile',
        category: 'Demographics',
        count: 'Verified',
        description: 'Demographics, validated identification, clinical emergency contact.',
        color: '#38bdf8',
        iconName: 'User',
      },
      {
        id: 'documents',
        label: 'Documents',
        category: 'Source Records',
        count: counts.documents ?? 3,
        description: 'Uploaded laboratory reports, consultation notes & clinical PDFs.',
        color: '#60a5fa',
        iconName: 'FileText',
      },
      {
        id: 'labs',
        label: 'Laboratory Results',
        category: 'Quantitative Labs',
        count: counts.labs ?? 12,
        description: 'Biochemical panels with report-derived reference intervals only.',
        color: '#10b981',
        iconName: 'FlaskConical',
      },
      {
        id: 'medications',
        label: 'Medications',
        category: 'Pharmacology',
        count: counts.medications ?? 4,
        description: 'Documented drug names, frequencies & dosage instructions.',
        color: '#a855f7',
        iconName: 'Pill',
      },
      {
        id: 'conditions',
        label: 'Conditions',
        category: 'Documented History',
        count: counts.conditions ?? 3,
        description: 'Reported past medical history & clinician documented diagnoses.',
        color: '#0284c7',
        iconName: 'ShieldAlert',
      },
      {
        id: 'allergies',
        label: 'Allergies',
        category: 'Hypersensitivities',
        count: counts.allergies ?? 2,
        description: 'Patient-reported and clinician-noted adverse substance reactions.',
        color: '#f59e0b',
        iconName: 'AlertTriangle',
      },
      {
        id: 'timeline',
        label: 'Timeline',
        category: 'Chronological',
        count: counts.timeline ?? 8,
        description: 'Longitudinal aggregation of clinical events and encounters.',
        color: '#14b8a6',
        iconName: 'Clock',
      },
      {
        id: 'conflicts',
        label: 'Conflicts',
        category: 'Discrepancies',
        count: counts.conflicts ?? 2,
        description: 'Cross-document discrepancies flagged for clinician verification.',
        color: '#ef4444',
        iconName: 'AlertCircle',
      },
      {
        id: 'ai-summary',
        label: 'AI Summary',
        category: 'Intelligence',
        count: counts.summary ?? 'AI',
        description: 'Non-diagnostic structured synthesis derived strictly from patient data.',
        color: '#8b5cf6',
        iconName: 'Sparkles',
      },
    ];

    const radius = 6.2;
    const total = rawNodes.length;
    return rawNodes.map((item, idx) => {
      const angle = (idx / total) * Math.PI * 2;
      // Slight vertical wobble for dynamic 3D depth
      const yOffset = Math.sin(idx * 1.5) * 1.2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      return {
        ...item,
        position: [x, yOffset, z] as [number, number, number],
      };
    });
  }, [counts]);

  const handleResetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
      controlsRef.current.target.set(0, 0, 0);
    }
  };

  const handleNodeClick = (nodeId: string) => {
    if (onSelectNode) {
      onSelectNode(nodeId);
    }
  };

  return (
    <div className="relative w-full rounded-2xl border border-cyan-500/20 bg-gradient-to-b from-slate-950 via-slate-900/90 to-slate-950 overflow-hidden shadow-2xl">
      {/* Top Overlay Controls & Title */}
      <div className="absolute top-4 left-4 right-4 z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-2 pointer-events-none">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 backdrop-blur-md">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-1.5">
              3D Clinical Information Graph
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                Interactive
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Information relationships topology • Drag to rotate • Scroll to zoom • Click node to open panel
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <button
            onClick={handleResetCamera}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700/80 text-xs text-slate-300 hover:text-white hover:border-cyan-500/50 backdrop-blur-md transition-all shadow-md"
            title="Reset View"
          >
            <RotateCcw className="w-3 h-3 text-cyan-400" />
            <span>Reset View</span>
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div style={{ height }}>
        <Canvas
          camera={{ position: [0, 4, 14], fov: 45 }}
          gl={{ antialias: true, alpha: true }}
        >
          <Scene
            nodes={nodes}
            patientName={patientName}
            patientMrn={patientMrn}
            hoveredId={hoveredId}
            onHover={setHoveredId}
            onSelect={handleNodeClick}
            controlsRef={controlsRef}
          />
        </Canvas>
      </div>

      {/* Bottom Medical Non-Diagnostic Guardrail Notice */}
      <div className="absolute bottom-3 left-4 right-4 z-10 flex items-center justify-between pointer-events-none text-[10px] text-slate-400 font-mono">
        <div className="flex items-center gap-1.5 bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800/80 backdrop-blur-md">
          <ShieldCheck className="w-3 h-3 text-cyan-400" />
          <span>Strict Non-Diagnostic: Graph represents document relationships, not disease severity or treatment.</span>
        </div>
        <div className="hidden md:flex items-center gap-2 bg-slate-950/80 px-2.5 py-1 rounded-md border border-slate-800/80 backdrop-blur-md">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Real-time WebGL Engine</span>
        </div>
      </div>
    </div>
  );
};
