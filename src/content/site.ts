import {
  BookOpenCheck,
  Cpu,
  GraduationCap,
  LibraryBig,
  PlayCircle,
  Route,
  ShieldCheck,
  Waves,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export const siteConfig = {
  name: 'SystemVerilog Academy',
  subtitle: 'Your VLSI Companion',
  domain: 'systemverilogacademy.com',
  youtubeUrl: 'https://www.youtube.com/c/SystemverilogAcademy/',
  linkedinUrl: 'https://www.linkedin.com/company/systemverilogacademy/',
  contactEmail: 'support@systemverilogacademy.com',
  description:
    'SystemVerilog, digital design, assertions, UVM, and verification learning resources for engineers building practical semiconductor skills.',
};

export type FeatureItem = {
  title: string;
  description: string;
  icon: LucideIcon;
};

export const heroHighlights = [
  '17K+ learner community',
  '17 course paths in the academy library',
  'Lessons now available through YouTube',
];

export type CoursePreview = {
  title: string;
  description: string;
  level: string;
  modules: number;
  lessons: number;
  topic: string;
  query: string;
};

export const coursePreviews: CoursePreview[] = [
  {
    title: 'SystemVerilog Beginner: Write Your First Design & TB Modules',
    description:
      'Start with modules, design blocks, testbench structure, and live coding habits before moving into deeper verification.',
    level: 'Beginner',
    modules: 13,
    lessons: 26,
    topic: 'SV basics',
    query: 'Systemverilog Beginner Write Your First Design TB Modules',
  },
  {
    title: 'SystemVerilog Design 1: Assignment Statements & Synthesis',
    description:
      'Understand assignment semantics, combinational and sequential intent, and the hardware that synthesis creates.',
    level: 'Intermediate',
    modules: 8,
    lessons: 21,
    topic: 'RTL design',
    query: 'Systemverilog Design Assignment Statements Synthesis',
  },
  {
    title: 'SystemVerilog Verification 1: Testbench Constructs',
    description:
      'Build the foundation for verification with practical SystemVerilog programming and testbench construction.',
    level: 'Beginner',
    modules: 8,
    lessons: 11,
    topic: 'Verification',
    query: 'Systemverilog Verification Testbench Constructs',
  },
  {
    title: 'Functional Coverage Coding in SystemVerilog',
    description:
      'Covergroups, coverpoints, bins, transition bins, illegal bins, crosses, and coverage-driven thinking.',
    level: 'Intermediate',
    modules: 14,
    lessons: 25,
    topic: 'Coverage',
    query: 'Functional Coverage Coding Systemverilog',
  },
  {
    title: 'Simulation Time Regions in Detail',
    description:
      'Active, NBA, observed, reactive, postponed, and the scheduling model that explains many simulation surprises.',
    level: 'Intermediate',
    modules: 10,
    lessons: 13,
    topic: 'Simulation',
    query: 'Simulation Time Regions Systemverilog',
  },
  {
    title: 'SystemVerilog Assertions: A Simplified Approach',
    description:
      'Immediate and concurrent assertions, clocking, implication operators, sequence operators, and practical SVA patterns.',
    level: 'Intermediate',
    modules: 14,
    lessons: 25,
    topic: 'SVA',
    query: 'Systemverilog Assertions Simplified Approach',
  },
  {
    title: 'UVM in SystemVerilog 1: Quick Start for Beginners',
    description:
      'A practical ramp into UVM structure, classes, testbench organization, and the bridge from pure SV to UVM.',
    level: 'Beginner',
    modules: 8,
    lessons: 17,
    topic: 'UVM',
    query: 'UVM in Systemverilog Quick start beginners',
  },
  {
    title: 'UVM in SystemVerilog 2: Writing Reusable Agents',
    description:
      'Professional agent structure, reusable components, transactions, drivers, monitors, sequencers, and config flow.',
    level: 'Intermediate',
    modules: 6,
    lessons: 16,
    topic: 'UVM agents',
    query: 'UVM Writing Reusable Agents Systemverilog',
  },
];

export const academyStats = [
  { value: '17', label: 'course paths in the academy library' },
  { value: '141', label: 'modules across the structured curriculum' },
  { value: '297', label: 'lessons being opened through the public relaunch' },
];

export const learningTracks: FeatureItem[] = [
  {
    title: 'Digital design foundations',
    description:
      'Strengthen timing, RTL structure, finite-state machines, testbenches, and the habits that make hardware code easier to reason about.',
    icon: Cpu,
  },
  {
    title: 'SystemVerilog practice',
    description:
      'Work through language concepts with grounded examples rather than collecting syntax in isolation.',
    icon: BookOpenCheck,
  },
  {
    title: 'Verification thinking',
    description:
      'Build the mental model for stimulus, checking, coverage, debug, and regression discipline before reaching for heavier tooling.',
    icon: Waves,
  },
  {
    title: 'Assertions and UVM',
    description:
      'Move from raw testbenches into SVA and UVM with courses that stay close to code, waveforms, and reusable structure.',
    icon: ShieldCheck,
  },
];

export const roadmapItems: FeatureItem[] = [
  {
    title: 'YouTube-first library',
    description:
      'Current public learning points to the academy channel while course material is made easier to browse and revisit.',
    icon: PlayCircle,
  },
  {
    title: 'Curated course paths',
    description:
      'The next public layer can organize lessons into beginner, design, verification, assertions, and UVM paths.',
    icon: Route,
  },
  {
    title: 'Hands-on learning platform',
    description:
      'Student accounts, progress, exercises, and private workspaces can return when the product is ready for them again.',
    icon: GraduationCap,
  },
  {
    title: 'Content library',
    description:
      'The future backend can own course metadata and publishing contracts while the frontend keeps rendering explicit public surfaces.',
    icon: LibraryBig,
  },
];
