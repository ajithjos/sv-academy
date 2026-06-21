import rawCourseCatalog from './courses.json';

export type CourseCategoryId = 'foundation' | 'rtl-design' | 'verification' | 'assertions' | 'uvm';

export type CourseCategory = {
  id: CourseCategoryId;
  label: string;
  shortLabel: string;
  description: string;
};

export type CatalogLessonStatus = 'available' | 'missing';

export type CatalogLesson = {
  id: string;
  index: number;
  title: string;
  status: CatalogLessonStatus;
  youtubeUrl: string | null;
  videoId: string | null;
  youtubeTitle: string | null;
  thumbnailUrl: string | null;
  durationText: string | null;
  durationSeconds: number | null;
};

export type CatalogModule = {
  id: string;
  index: number;
  slug: string;
  title: string;
  lessonCount: number;
  availableLessonCount: number;
  durationText: string | null;
  lessons: CatalogLesson[];
};

export type CatalogCourse = {
  id: string;
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  category: CourseCategory;
  counts: {
    modules: number;
    lessons: number;
    availableLessons: number;
    missingLessons: number;
  };
  youtube: {
    channelHandle: string;
    playlistId: string | null;
    playlistUrl: string | null;
    playlistTitle: string | null;
    playlistVideoCount: number | null;
  };
  thumbnailUrl: string;
  firstLesson: CatalogLesson | null;
  durationText: string | null;
  mappingStatus: string;
  modules: CatalogModule[];
};

export type CatalogStats = {
  snapshotDate: string;
  courseCount: number;
  moduleCount: number;
  lessonCount: number;
  availableLessonCount: number;
  missingLessonCount: number;
};

type RawCourseCatalog = {
  metadata: {
    snapshotDate: string;
    summary?: {
      catalogCourseCount?: number;
      catalogModuleCount?: number;
      catalogLessonCount?: number;
      mappedLessonCount?: number;
      missingLessonCount?: number;
    };
  };
  courses: RawCourse[];
};

type RawCourse = {
  id: string;
  slug: string;
  title: string;
  subtitle?: string;
  description?: string;
  counts?: {
    modules?: number;
    lessons?: number;
  };
  youtube?: {
    channelHandle?: string;
    playlistId?: string | null;
    playlistUrl?: string | null;
    playlistTitle?: string | null;
    playlistVideoCount?: number | null;
  };
  metadata?: {
    sync?: {
      mappingStatus?: string;
      missingLessonCount?: number;
    };
  };
  modules: RawModule[];
};

type RawModule = {
  index: number;
  slug: string;
  title: string;
  lessonCount?: number;
  lessons: RawLesson[];
};

type RawLesson = {
  index: number;
  title: string;
  youtube?: {
    videoId?: string | null;
    url?: string | null;
    title?: string | null;
    thumbnailUrl?: string | null;
    durationText?: string | null;
  };
  metadata?: {
    sync?: {
      status?: string;
    };
  };
};

const courseCatalog = rawCourseCatalog as RawCourseCatalog;

export const courseCategories: CourseCategory[] = [
  {
    id: 'foundation',
    label: 'Foundations',
    shortLabel: 'Foundations',
    description: 'First steps in VLSI, SystemVerilog syntax, modules, and testbench basics.',
  },
  {
    id: 'rtl-design',
    label: 'RTL Design',
    shortLabel: 'Design',
    description: 'Synthesizable SystemVerilog, assignment semantics, and RTL code structure.',
  },
  {
    id: 'verification',
    label: 'Verification',
    shortLabel: 'Verification',
    description: 'Testbench construction, OOP, randomization, coverage, and simulation semantics.',
  },
  {
    id: 'assertions',
    label: 'Assertions',
    shortLabel: 'SVA',
    description: 'Immediate and concurrent assertions, sequences, implication, and reusable checks.',
  },
  {
    id: 'uvm',
    label: 'UVM',
    shortLabel: 'UVM',
    description: 'UVM structure, reusable agents, transactions, drivers, monitors, and VIP design.',
  },
];

const categoryById = new Map(courseCategories.map((category) => [category.id, category]));

const preferredCourseOrder = [
  'systemverilog-for-absolute-beginner',
  'systemverilog-essentials',
  'systemverilog-beginner-write-your-first-design-and-tb-modules',
  'systemverilog-design-1-assignment-statements-and-synthesis',
  'systemverilog-design-2-systemverilog-features-for-rtl-coding',
  'systemverilog-design-3-a-profession-soc-rtl-code-walkthrough',
  'systemverilog-verification-1-start-learning-testbench-constructs',
  'systemverilog-verification-2-learn-more-testbench-constructs',
  'systemverilog-verification-3-object-oriented-programming-in-sv',
  'systemverilog-verification-4-build-your-random-testbench-in-sv',
  'systemverilog-verification-5-functional-coverage-coding-in-sv',
  'systemverilog-verification-6-simulation-time-regions-in-detail',
  'systemverilog-verification-7-converting-module-based-tb-to-class-based',
  'systemverilog-assertions-a-simplified-approach-to-master',
  'systemverilog-assertions',
  'uvm-in-systemverilog-1-quick-start-for-absolute-beginners',
  'uvm-beginner',
  'uvm-in-systemverilog-2-writing-reusable-agents-in-uvm',
  'uvm-in-systemverilog-3-learn-the-architecture-and-code-your-vip',
];

const featuredCourseSlugs = [
  'systemverilog-for-absolute-beginner',
  'systemverilog-beginner-write-your-first-design-and-tb-modules',
  'systemverilog-design-1-assignment-statements-and-synthesis',
  'systemverilog-verification-1-start-learning-testbench-constructs',
  'systemverilog-verification-5-functional-coverage-coding-in-sv',
  'systemverilog-assertions-a-simplified-approach-to-master',
  'uvm-in-systemverilog-1-quick-start-for-absolute-beginners',
  'uvm-in-systemverilog-2-writing-reusable-agents-in-uvm',
];

function getCategoryForCourse(course: RawCourse): CourseCategory {
  const title = course.title.toLowerCase();

  if (title.includes('beginner') || title.includes('absolute') || title.includes('essential')) {
    return categoryById.get('foundation')!;
  }

  if (title.includes('uvm')) {
    return categoryById.get('uvm')!;
  }

  if (title.includes('assertion')) {
    return categoryById.get('assertions')!;
  }

  if (title.includes('design') || title.includes('rtl')) {
    return categoryById.get('rtl-design')!;
  }

  if (
    title.includes('verification') ||
    title.includes('coverage') ||
    title.includes('simulation')
  ) {
    return categoryById.get('verification')!;
  }

  return categoryById.get('foundation')!;
}

function parseDurationText(durationText?: string | null): number | null {
  if (!durationText) {
    return null;
  }

  const parts = durationText
    .split(':')
    .map((part) => Number.parseInt(part, 10))
    .filter((part) => Number.isFinite(part));

  if (parts.length === 0) {
    return null;
  }

  return parts.reduce((total, part) => total * 60 + part, 0);
}

function formatDuration(totalSeconds: number): string | null {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    return null;
  }

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes.toString().padStart(2, '0')}m`;
  }

  return `${Math.max(1, minutes)}m`;
}

function thumbnailForVideo(videoId?: string | null): string | null {
  return videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : null;
}

function getCourseFallbackThumbnail(category: CourseCategory): string {
  switch (category.id) {
    case 'rtl-design':
      return '/images/legacy-home-image2.jpg';
    case 'uvm':
      return '/images/sva-hero-lab.png';
    default:
      return '/images/legacy-home-image1.jpg';
  }
}

function normalizeLesson(course: RawCourse, module: RawModule, lesson: RawLesson): CatalogLesson {
  const videoId = lesson.youtube?.videoId ?? null;
  const youtubeUrl = lesson.youtube?.url ?? (videoId ? `https://www.youtube.com/watch?v=${videoId}` : null);
  const status = youtubeUrl ? 'available' : 'missing';
  const durationText = lesson.youtube?.durationText ?? null;

  return {
    id: `${course.slug}-m${module.index}-l${lesson.index}`,
    index: lesson.index,
    title: lesson.title,
    status,
    youtubeUrl,
    videoId,
    youtubeTitle: lesson.youtube?.title ?? null,
    thumbnailUrl: lesson.youtube?.thumbnailUrl ?? thumbnailForVideo(videoId),
    durationText,
    durationSeconds: parseDurationText(durationText),
  };
}

function normalizeCourse(course: RawCourse): CatalogCourse {
  const category = getCategoryForCourse(course);
  const modules = course.modules.map((module) => {
    const lessons = module.lessons.map((lesson) => normalizeLesson(course, module, lesson));
    const availableLessonCount = lessons.filter((lesson) => lesson.status === 'available').length;
    const moduleDurationSeconds = lessons.reduce(
      (total, lesson) => total + (lesson.durationSeconds ?? 0),
      0,
    );

    return {
      id: `${course.slug}-m${module.index}`,
      index: module.index,
      slug: module.slug,
      title: module.title,
      lessonCount: module.lessonCount ?? lessons.length,
      availableLessonCount,
      durationText: formatDuration(moduleDurationSeconds),
      lessons,
    };
  });

  const lessons = modules.flatMap((module) => module.lessons);
  const availableLessons = lessons.filter((lesson) => lesson.status === 'available');
  const firstLesson = availableLessons[0] ?? null;
  const totalDurationSeconds = lessons.reduce(
    (total, lesson) => total + (lesson.durationSeconds ?? 0),
    0,
  );

  return {
    id: course.id,
    slug: course.slug,
    title: course.title,
    subtitle: course.subtitle ?? '',
    description: course.description ?? 'Structured SystemVerilog Academy lessons on YouTube.',
    category,
    counts: {
      modules: course.counts?.modules ?? modules.length,
      lessons: course.counts?.lessons ?? lessons.length,
      availableLessons: availableLessons.length,
      missingLessons: lessons.length - availableLessons.length,
    },
    youtube: {
      channelHandle: course.youtube?.channelHandle ?? '@SystemverilogAcademy',
      playlistId: course.youtube?.playlistId ?? null,
      playlistUrl: course.youtube?.playlistUrl ?? null,
      playlistTitle: course.youtube?.playlistTitle ?? null,
      playlistVideoCount: course.youtube?.playlistVideoCount ?? null,
    },
    thumbnailUrl:
      firstLesson?.thumbnailUrl ?? thumbnailForVideo(firstLesson?.videoId) ?? getCourseFallbackThumbnail(category),
    firstLesson,
    durationText: formatDuration(totalDurationSeconds),
    mappingStatus: course.metadata?.sync?.mappingStatus ?? 'catalog_course',
    modules,
  };
}

function courseSortValue(course: CatalogCourse): number {
  const index = preferredCourseOrder.indexOf(course.slug);
  if (index >= 0) {
    return index;
  }

  const categoryIndex = courseCategories.findIndex((category) => category.id === course.category.id);
  return 1000 + categoryIndex * 100;
}

const catalogCourses = courseCatalog.courses
  .map(normalizeCourse)
  .sort(
    (left, right) => courseSortValue(left) - courseSortValue(right) || left.title.localeCompare(right.title),
  );

export function getCatalogCourses(): CatalogCourse[] {
  return catalogCourses;
}

export function getFeaturedCourses(): CatalogCourse[] {
  const courseBySlug = new Map(catalogCourses.map((course) => [course.slug, course]));
  return featuredCourseSlugs
    .map((slug) => courseBySlug.get(slug))
    .filter((course): course is CatalogCourse => Boolean(course));
}

export function getCourseBySlug(slug: string): CatalogCourse | null {
  return catalogCourses.find((course) => course.slug === slug) ?? null;
}

export function getRelatedCourses(course: CatalogCourse, limit = 3): CatalogCourse[] {
  const related = catalogCourses.filter(
    (candidate) => candidate.slug !== course.slug && candidate.category.id === course.category.id,
  );
  const fallback = catalogCourses.filter(
    (candidate) => candidate.slug !== course.slug && candidate.category.id !== course.category.id,
  );

  return [...related, ...fallback].slice(0, limit);
}

export function getCatalogStats(): CatalogStats {
  const summary = courseCatalog.metadata.summary;
  const lessonCount = catalogCourses.reduce((total, course) => total + course.counts.lessons, 0);
  const availableLessonCount = catalogCourses.reduce(
    (total, course) => total + course.counts.availableLessons,
    0,
  );

  return {
    snapshotDate: courseCatalog.metadata.snapshotDate,
    courseCount: summary?.catalogCourseCount ?? catalogCourses.length,
    moduleCount:
      summary?.catalogModuleCount ??
      catalogCourses.reduce((total, course) => total + course.counts.modules, 0),
    lessonCount: summary?.catalogLessonCount ?? lessonCount,
    availableLessonCount: summary?.mappedLessonCount ?? availableLessonCount,
    missingLessonCount: summary?.missingLessonCount ?? lessonCount - availableLessonCount,
  };
}
