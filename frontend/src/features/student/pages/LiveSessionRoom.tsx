import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, AlertCircle } from "lucide-react";
import { Button, PageSpinner } from "../../../components/ui";
import { liveSessionApi } from "../../../api/liveSessionApi";

export default function LiveSessionRoom() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [meetingUrl, setMeetingUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    liveSessionApi
      .join(Number(sessionId))
      .then((res: any) => {
        setMeetingUrl(res.meeting_url);
      })
      .catch((err: any) => {
        setError(err?.message || t("student.liveSessions.joinError"));
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <PageSpinner />;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-500" />
        </div>
        <p className="text-navy font-medium">{error}</p>
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4" />
          {t("student.liveSessions.goBack")}
        </Button>
      </div>
    );
  }

  const iframeSrc = `${meetingUrl}?config.prejoinPageEnabled=true&config.requireDisplayName=true`;

  return (
    <div className="relative w-full h-screen">
      <button
        onClick={() => navigate(-1)}
        className="absolute top-4 left-4 z-50 flex items-center gap-2 px-4 py-2 bg-white/90 backdrop-blur-sm rounded-xl shadow-lg text-navy text-sm font-medium hover:bg-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        {t("student.liveSessions.leave")}
      </button>

      <iframe
        src={iframeSrc}
        className="w-full h-full border-0"
        allow="camera; microphone; fullscreen; display-capture; autoplay"
        title="Live Session"
      />
    </div>
  );
}
