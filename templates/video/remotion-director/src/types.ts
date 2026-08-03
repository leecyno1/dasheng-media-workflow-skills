export type SceneAudio = {
  duck_bgm?: boolean;
  sfx?: string | null;
  sfx_src?: string;
  voice_priority?: string;
};

export type VisualPayload = {
  asset_id?: string;
  evidence_relation?: string;
  evidence_confidence?: string;
  disclosure?: string;
  display_mode?: 'clean' | 'keyword_only' | 'card';
  eyebrow?: string;
  headline?: string;
  source?: string;
  series?: Array<{name: string; color?: string; values: number[]}>;
  labels?: string[];
  metrics?: Array<{label: string; value: number; peer?: string; peer_value?: number}>;
  unit?: string;
  document_src?: string;
  document_title?: string;
  callouts?: string[];
  columns?: string[];
  rows?: string[][];
  nodes?: string[];
  tasks?: string[];
  broll_src?: string;
  broll_start_sec?: number;
  context?: string;
  left?: {title: string; value: string};
  right?: {title: string; value: string};
  points?: string[];
  keywords?: string[];
};

export type DirectorScene = {
  id: string;
  title: string;
  narration?: string;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
  beat_class: string;
  template_id: string;
  speaker_state: string;
  material_state: string;
  pip_shape: string;
  transition_in: string;
  transition_out: string;
  html_animation_behavior: string;
  audio: SceneAudio;
  visual?: VisualPayload;
  speaker_object_position?: string;
  camera?: {scale?: number; x?: number; y?: number};
};

export type DirectorPlan = {
  title?: string;
  fps?: number;
  width?: number;
  height?: number;
  source_video?: string;
  bgm_src?: string;
  voice_gain?: number;
  speaker_object_position?: string;
  scenes: DirectorScene[];
};

export type FamilyProps = {
  scene: DirectorScene;
  motionBehavior: string;
};
