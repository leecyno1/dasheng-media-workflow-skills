import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FAMILY_COMPONENTS} from './families';
import type {DirectorPlan, DirectorScene} from './types';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const transitionEnvelope = (scene: DirectorScene, frame: number, duration: number, fps: number) => {
  const enter = interpolate(frame, [0, Math.min(14, duration / 3)], [0, 1], clamp);
  const exit = interpolate(frame, [Math.max(0, duration - 10), duration], [1, 0], clamp);
  const transition_in = scene.transition_in || 'hard_cut';
  const transition_out = scene.transition_out || 'hard_cut';
  const enterOpacity = transition_in === 'cross_dissolve' || transition_in === 'hard_cut'
    ? 1
    : transition_in.includes('fade')
      ? 0.35 + enter * 0.65
      : 1;
  const push = transition_in.includes('push') ? (1 - enter) * 120 : 0;
  const settle = spring({frame, fps, config: {damping: 180, stiffness: 120, mass: 0.8}});
  const exitSettle = transition_out.includes('resolve') ? (1 - exit) * 0.01 : 0;
  const scale = (transition_in.includes('morph') ? 0.94 + settle * 0.06 : 1) - exitSettle;
  // Non-overlapping Sequences cannot use a zero-area reveal without flashing the root background.
  const clipPath = 'inset(0%)';
  return {
    opacity: enterOpacity,
    transform: `translateX(${push}px) scale(${scale})`,
    clipPath,
  };
};

const speakerBox = (scene: DirectorScene): React.CSSProperties => {
  const speaker_state = scene.speaker_state || 'full';
  const pip_shape = scene.pip_shape || 'none';
  const shapeRadius = pip_shape === 'circle' ? '50%' : pip_shape === 'square' ? 12 : 34;
  if (speaker_state === 'hidden') return {display: 'none'};
  if (speaker_state === 'circle_pip') {
    return {right: 64, bottom: 62, width: 300, height: 300, borderRadius: '50%'};
  }
  if (speaker_state === 'rounded_rect_pip') {
    return {right: 64, bottom: 58, width: 430, height: 300, borderRadius: shapeRadius};
  }
  if (speaker_state === 'vertical_strip') {
    return {right: 0, top: 0, bottom: 0, width: 470, borderRadius: 0};
  }
  if (speaker_state === 'half_left') {
    return {left: 0, top: 0, bottom: 0, width: '52%', borderRadius: 0};
  }
  if (speaker_state === 'half_right') {
    return {right: 0, top: 0, bottom: 0, width: '52%', borderRadius: 0};
  }
  return {inset: 0, borderRadius: pip_shape === 'nested_card' ? 36 : 0};
};

const MasterVoiceTrack: React.FC<{sourceVideo: string; voiceGain: number}> = ({sourceVideo, voiceGain}) => {
  return <Audio src={staticFile(sourceVideo)} volume={voiceGain} />;
};

const SpeakerLayer: React.FC<{
  scene: DirectorScene;
  sourceVideo: string;
  sourceStartFrame: number;
  speakerObjectPosition: string;
}> = ({scene, sourceVideo, sourceStartFrame, speakerObjectPosition}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!sourceVideo || scene.speaker_state === 'hidden') return null;
  const entry = spring({frame, fps, config: {damping: 180, stiffness: 130}});
  const box = speakerBox(scene);
  const cameraScale = scene.camera?.scale ?? (scene.speaker_state === 'speaker_punch_in' ? 1.08 : 1);
  const cameraX = (scene.camera?.x ?? 0) * 100;
  const cameraY = (scene.camera?.y ?? 0) * 100;
  return (
    <div
      style={{
        position: 'absolute',
        overflow: 'hidden',
        background: '#14221f',
        boxShadow: scene.speaker_state.includes('pip') ? '0 20px 65px rgba(16,32,27,.32)' : undefined,
        border: scene.speaker_state.includes('pip') ? '3px solid rgba(255,255,255,.82)' : undefined,
        transform: `translateY(${(1 - entry) * 24}px)`,
        zIndex: scene.speaker_state.includes('pip') ? 3 : 1,
        ...box,
      }}
    >
      <OffthreadVideo
        src={staticFile(sourceVideo)}
        startFrom={sourceStartFrame}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: scene.speaker_object_position || speakerObjectPosition,
          transform: `translate(${cameraX}%, ${cameraY}%) scale(${cameraScale})`,
          transformOrigin: scene.speaker_object_position || speakerObjectPosition,
        }}
      />
    </div>
  );
};

const SceneEvidenceMediaLayer: React.FC<{scene: DirectorScene}> = ({scene}) => {
  const {fps} = useVideoConfig();
  const visual = scene.visual || {};
  const isVox = scene.template_id === 'vox-editorial-collage';
  const backgroundStart = Math.max(0, Math.round((visual.background_video_start_sec || 0) * fps));
  const pipStart = Math.max(0, Math.round((visual.pip_video_start_sec || 0) * fps));
  return (
    <>
      {visual.background_video_src ? (
        <AbsoluteFill style={{zIndex: 0, overflow: 'hidden'}}>
          <OffthreadVideo
            src={staticFile(visual.background_video_src)}
            startFrom={backgroundStart}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover', opacity: visual.background_video_opacity ?? 0.72}}
          />
          <AbsoluteFill style={{background: `rgba(12,24,21,${visual.background_video_scrim ?? 0.24})`}} />
        </AbsoluteFill>
      ) : null}
      {visual.pip_video_src && !isVox ? (
        <div style={{position: 'absolute', right: 62, bottom: 62, width: 430, height: 252, zIndex: 4, overflow: 'hidden', borderRadius: 22, border: '3px solid rgba(255,255,255,.9)', background: '#14211d', boxShadow: '0 22px 70px rgba(10,22,18,.32)'}}>
          <OffthreadVideo
            src={staticFile(visual.pip_video_src)}
            startFrom={pipStart}
            muted
            style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: visual.pip_video_object_position || '50% 50%'}}
          />
        </div>
      ) : null}
    </>
  );
};

const captionChunks = (text: string) => {
  const phrases = text.split(/(?<=[。！？；])/u).map((item) => item.trim()).filter(Boolean);
  return phrases.flatMap((phrase) => {
    if (phrase.length <= 24) return [phrase];
    const parts = phrase.split(/(?<=[，、：])/u).map((item) => item.trim()).filter(Boolean);
    return parts.length > 1 ? parts : [phrase];
  });
};

const CaptionLayer: React.FC<{scene: DirectorScene; durationInFrames: number}> = ({scene, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localMs = frame / fps * 1000;
  const timedCaption = scene.captions?.find((cue) => localMs >= cue.startMs && localMs < cue.endMs);
  const chunks = captionChunks(scene.narration || '');
  const fallbackIndex = chunks.length
    ? Math.min(chunks.length - 1, Math.floor((frame / Math.max(1, durationInFrames)) * chunks.length))
    : -1;
  const text = timedCaption?.text || (fallbackIndex >= 0 ? chunks[fallbackIndex] : '');
  if (!text) return null;
  const isVox = scene.template_id === 'vox-editorial-collage';
  return (
    <div style={{position: 'absolute', left: isVox ? 230 : 180, right: isVox ? 230 : 180, bottom: 34, zIndex: 6, textAlign: 'center', pointerEvents: 'none'}}>
      <span style={{display: 'inline', padding: isVox ? '6px 13px 8px' : '8px 16px 10px', borderRadius: isVox ? 4 : 12, background: isVox ? 'rgba(16,13,10,.62)' : 'rgba(10,18,16,.78)', color: 'white', fontSize: isVox ? 29 : 31, lineHeight: 1.55, fontWeight: 750, letterSpacing: '0.02em', boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone', textShadow: '0 2px 8px rgba(0,0,0,.55)'}}>
        {text}
      </span>
    </div>
  );
};

const cueVisible = (localMs: number, cue: {startMs: number; endMs: number}) =>
  localMs >= cue.startMs && localMs < cue.endMs;

const VoxTextOverlayLayer: React.FC<{scene: DirectorScene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (scene.template_id !== 'vox-editorial-collage') return null;
  const localMs = frame / fps * 1000;
  const visual = scene.visual || {};
  const emphasis = (visual.emphasis_cues || []).filter((cue) => cueVisible(localMs, cue));
  const labels = (visual.entity_labels || []).filter((cue) => cueVisible(localMs, cue));
  const palette = {
    red: {background: '#d84b3e', color: '#fff8e8'},
    gold: {background: '#f2ca52', color: '#201a12'},
    cream: {background: '#f4ead4', color: '#201a12'},
    ink: {background: '#201a12', color: '#fff8e8'},
  };
  return (
    <AbsoluteFill style={{zIndex: 5, pointerEvents: 'none'}}>
      {emphasis.map((cue, index) => {
        const style = palette[cue.tone || 'gold'];
        const progress = spring({frame: Math.max(0, frame - Math.round(cue.startMs / 1000 * fps)), fps, config: {damping: 15, stiffness: 190}});
        return (
          <div key={`emphasis-${index}`} style={{position: 'absolute', left: `${cue.x ?? 50}%`, top: `${cue.y ?? 18}%`, transform: `translate(-50%, -50%) rotate(-2deg) scale(${0.82 + progress * 0.18})`, padding: '12px 22px 10px', border: '4px solid #201a12', boxShadow: '7px 7px 0 rgba(32,26,18,.28)', fontSize: 52, lineHeight: 1.08, fontWeight: 950, letterSpacing: '.04em', ...style}}>
            {cue.text}
          </div>
        );
      })}
      {labels.map((cue, index) => {
        const style = palette[cue.tone || 'cream'];
        return (
          <div key={`entity-${index}`} style={{position: 'absolute', left: `${cue.x ?? 50}%`, top: `${cue.y ?? 50}%`, transform: 'translate(-50%, -50%) rotate(-1deg)', padding: '7px 13px 6px', border: '3px solid #201a12', boxShadow: '4px 4px 0 rgba(32,26,18,.22)', fontSize: 27, lineHeight: 1.1, fontWeight: 900, ...style}}>
            {cue.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneClip: React.FC<{
  scene: DirectorScene;
  sourceVideo: string;
  sourceStartFrame: number;
  speakerObjectPosition: string;
  durationInFrames: number;
}> = ({scene, sourceVideo, sourceStartFrame, speakerObjectPosition, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const Family = FAMILY_COMPONENTS[scene.template_id] ?? FAMILY_COMPONENTS['speaker-anchor'];
  const material_state = scene.material_state || 'none';
  const style = transitionEnvelope(scene, frame, durationInFrames, fps);
  const transparent = material_state === 'none' || material_state === 'transparent_overlay';
  const html_animation_behavior = scene.html_animation_behavior || 'default_motion';
  const audio = scene.audio || {};
  return (
    <AbsoluteFill style={{...style, background: transparent ? 'transparent' : '#eef0e8'}}>
      <SceneEvidenceMediaLayer scene={scene} />
      <SpeakerLayer
        scene={scene}
        sourceVideo={sourceVideo}
        sourceStartFrame={sourceStartFrame}
        speakerObjectPosition={speakerObjectPosition}
      />
      <AbsoluteFill style={{zIndex: 2, pointerEvents: 'none'}}>
        <Family scene={scene} motionBehavior={html_animation_behavior} />
      </AbsoluteFill>
      <VoxTextOverlayLayer scene={scene} />
      <CaptionLayer scene={scene} durationInFrames={durationInFrames} />
      {audio.sfx_src ? <Audio src={staticFile(audio.sfx_src)} volume={0.2} /> : null}
    </AbsoluteFill>
  );
};

export const DirectorVideo: React.FC<DirectorPlan> = ({
  scenes,
  source_video = '',
  bgm_src = '',
  voice_gain = 1,
  speaker_object_position = '50% 50%',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const active =
    scenes.find((scene) => frame >= Math.round(scene.start_sec * fps) && frame < Math.round(scene.end_sec * fps)) ??
    scenes[scenes.length - 1];
  const bgmVolume = active?.audio?.duck_bgm ? 0.035 : 0.055;
  return (
    <AbsoluteFill style={{background: '#e9ece5', fontFamily: 'Avenir Next, PingFang SC, sans-serif', color: '#15201d'}}>
      {/* Keep speech outside scene Sequences so visual cuts never remount the audible track. */}
      {source_video ? <MasterVoiceTrack sourceVideo={source_video} voiceGain={voice_gain} /> : null}
      {bgm_src ? <Audio src={staticFile(bgm_src)} loop volume={bgmVolume} /> : null}
      {scenes.map((scene, index) => {
        const from = Math.round(scene.start_sec * fps);
        // Derive each duration from adjacent absolute frame boundaries. Rounding a
        // start and a floating-point duration separately can leave a one-frame gap.
        const nextBoundary = index + 1 < scenes.length
          ? Math.round(scenes[index + 1].start_sec * fps)
          : Math.round(scene.end_sec * fps);
        const duration = Math.max(1, nextBoundary - from);
        return (
          <Sequence key={scene.id} from={from} durationInFrames={duration} premountFor={fps}>
            <SceneClip
              scene={scene}
              sourceVideo={source_video}
              sourceStartFrame={from}
              speakerObjectPosition={speaker_object_position}
              durationInFrames={duration}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
