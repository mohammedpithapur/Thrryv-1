import React, { useState, useRef, useEffect } from 'react';
import { Pause, Volume2, VolumeX } from 'lucide-react';

const VideoPlayer = ({
  src,
  className = '',
  autoPlay = false,
  fit = 'cover',
  screenFit = false
}) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [isMuted, setIsMuted] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (autoPlay && videoRef.current) {
      videoRef.current.play().catch(() => {
        setIsPlaying(false);
      });
    }
  }, [autoPlay]);

  const handleVideoClick = (e) => {
    e.stopPropagation();
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        videoRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const toggleMute = (e) => {
    e.stopPropagation();
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const percent = (videoRef.current.currentTime / videoRef.current.duration) * 100;
      setProgress(percent || 0);
    }
  };

  const isContain = fit === 'contain';
  const videoClassName = screenFit
    ? isContain
      ? 'w-full h-full object-contain'
      : 'w-full h-full object-cover'
    : isContain
      ? 'w-full h-auto object-contain'
      : 'w-full h-full object-cover';

  const containerStyle = screenFit
    ? { aspectRatio: '9 / 16', maxHeight: '70vh' }
    : undefined;

  return (
    <div
      className={`relative bg-black overflow-hidden ${className}`}
      style={containerStyle}
      onClick={handleVideoClick}
    >
      <video
        ref={videoRef}
        src={src}
        className={videoClassName}
        muted={isMuted}
        loop
        playsInline
        onTimeUpdate={handleTimeUpdate}
      />
      
      {/* Pause Icon Overlay */}
      {!isPlaying && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-20 h-20 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center">
            <Pause size={40} className="text-black" fill="black" />
          </div>
        </div>
      )}

      {/* Progress Bar at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
        <div
          className="h-full bg-white transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Mute/Unmute Button - Bottom Right */}
      <button
        onClick={toggleMute}
        className="absolute bottom-2 right-2 p-2 rounded-full bg-black/50 backdrop-blur-sm text-white hover:bg-black/70 transition-all z-10"
      >
        {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
      </button>
    </div>
  );
};

export default VideoPlayer;
