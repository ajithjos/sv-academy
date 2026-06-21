import {
  BookOpenCheck,
  Cpu,
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
  contactEmail: 'hello@system.academy.com',
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
  '19 public course paths',
  '309 videos organized by course',
];

export const learningTracks: FeatureItem[] = [
  {
    title: 'Digital design foundations',
    description:
      'Start with VLSI context, modules, signals, testbenches, and the basic habits behind clear hardware code.',
    icon: Cpu,
  },
  {
    title: 'SystemVerilog practice',
    description:
      'Work through the language with examples that stay close to code, simulation, and everyday RTL or testbench use.',
    icon: BookOpenCheck,
  },
  {
    title: 'Verification thinking',
    description:
      'Build a practical base in stimulus, checking, coverage, randomization, and simulation behavior.',
    icon: Waves,
  },
  {
    title: 'Assertions and UVM',
    description:
      'Move into SVA and UVM with courses organized around reusable structure and real verification code.',
    icon: ShieldCheck,
  },
];

export const roadmapItems: FeatureItem[] = [
  {
    title: 'Course index',
    description:
      'Use this site as the organized index for the academy courses, modules, and lessons.',
    icon: LibraryBig,
  },
  {
    title: 'Clear paths',
    description:
      'Start with foundations, then move into RTL design, verification, assertions, and UVM.',
    icon: Route,
  },
  {
    title: 'Video lessons',
    description:
      'Lessons open on YouTube, while the course pages keep the sequence easy to follow.',
    icon: PlayCircle,
  },
  {
    title: 'Reference point',
    description:
      'Bookmark a course page when you want to return to the same module or lesson later.',
    icon: BookOpenCheck,
  },
];
