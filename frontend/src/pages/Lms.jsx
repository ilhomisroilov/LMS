import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/axios";
import Modal from "../components/Modal.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { canAccess } from "../utils/authz.js";

export default function Lms() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isStudent = user?.role === "student";
  const canWriteCourses = canAccess(user, { permissions: ["course:write"] });
  const [courses, setCourses] = useState([]);
  const [active, setActive] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [myLessons, setMyLessons] = useState([]);
  const [courseOpen, setCourseOpen] = useState(false);
  const [lessonOpen, setLessonOpen] = useState(false);
  const [course, setCourse] = useState({ name: "", description: "" });
  const [lesson, setLesson] = useState({ title: "", content_type: "text", content: "", order_index: 1 });

  const loadCourses = () => api.get("/courses", { params: { size: 50 } }).then((r) => {
    setCourses(r.data.items);
    if (!active && r.data.items.length) setActive(r.data.items[0]);
  });
  useEffect(() => {
    if (isStudent) {
      api.get("/me/lessons").then((r) => setMyLessons(r.data));
      return;
    }
    loadCourses();
  }, [isStudent]);
  useEffect(() => {
    if (!isStudent && active) {
      api.get(`/courses/${active.id}/lessons`).then((r) => setLessons(r.data));
    }
  }, [active, isStudent]);

  const createCourse = async (e) => {
    e.preventDefault();
    const { data } = await api.post("/courses", course);
    setCourseOpen(false); setCourse({ name: "", description: "" });
    await loadCourses(); setActive(data);
  };
  const createLesson = async (e) => {
    e.preventDefault();
    await api.post("/courses/lessons", { ...lesson, course_id: active.id, order_index: Number(lesson.order_index) });
    setLessonOpen(false);
    api.get(`/courses/${active.id}/lessons`).then((r) => setLessons(r.data));
  };

  if (isStudent) {
    return (
      <div>
        <h1 className="mb-4 text-2xl font-bold">{t("lms.title")}</h1>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <ul className="divide-y divide-slate-100">
            {myLessons.map((lesson) => (
              <li key={lesson.id} className="flex items-center justify-between px-4 py-3">
                <span>
                  <span className="mr-2 text-slate-400">{lesson.order_index}.</span>
                  {lesson.title}
                </span>
                <span className="badge bg-slate-100 text-slate-600">{lesson.content_type}</span>
              </li>
            ))}
            {myLessons.length === 0 && (
              <li className="px-4 py-3 text-sm text-slate-400">{t("common.no_data")}</li>
            )}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("lms.title")}</h1>
        {canWriteCourses && (
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={() => setCourseOpen(true)}>+ {t("lms.add_course")}</button>
            {active && <button className="btn-primary" onClick={() => setLessonOpen(true)}>+ {t("lms.add_lesson")}</button>}
          </div>
        )}
      </div>
      <div className="grid grid-cols-4 gap-4">
        <div className="card col-span-1">
          <div className="mb-2 text-sm font-semibold text-slate-500">{t("lms.courses")}</div>
          <ul className="space-y-1">
            {courses.map((c) => (
              <li key={c.id}>
                <button onClick={() => setActive(c)}
                        className={`w-full rounded-lg px-3 py-2 text-left text-sm ${active?.id === c.id ? "bg-brand-light text-brand-dark" : "hover:bg-slate-100"}`}>
                  {c.name} <span className="text-xs text-slate-400">({c.lesson_count})</span>
                </button>
              </li>
            ))}
            {courses.length === 0 && <li className="text-sm text-slate-400">{t("common.no_data")}</li>}
          </ul>
        </div>
        <div className="card col-span-3">
          <div className="mb-2 text-sm font-semibold text-slate-500">{t("lms.lessons")} — {active?.name}</div>
          <ul className="divide-y divide-slate-100">
            {lessons.map((l) => (
              <li key={l.id} className="flex items-center justify-between py-2">
                <span><span className="text-slate-400">{l.order_index}.</span> {l.title}</span>
                <span className="badge bg-slate-100 text-slate-600">{l.content_type}</span>
              </li>
            ))}
            {lessons.length === 0 && <li className="py-2 text-sm text-slate-400">{t("common.no_data")}</li>}
          </ul>
        </div>
      </div>

      <Modal open={courseOpen} title={t("lms.add_course")} onClose={() => setCourseOpen(false)}>
        <form onSubmit={createCourse} className="space-y-3">
          <input className="input" placeholder={t("lms.courses")} value={course.name}
                 onChange={(e) => setCourse({ ...course, name: e.target.value })} required />
          <textarea className="input" placeholder={t("lms.content")} value={course.description}
                    onChange={(e) => setCourse({ ...course, description: e.target.value })} />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setCourseOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>

      <Modal open={lessonOpen} title={t("lms.add_lesson")} onClose={() => setLessonOpen(false)}>
        <form onSubmit={createLesson} className="space-y-3">
          <input className="input" placeholder={t("lms.lesson_title")} value={lesson.title}
                 onChange={(e) => setLesson({ ...lesson, title: e.target.value })} required />
          <select className="input" value={lesson.content_type}
                  onChange={(e) => setLesson({ ...lesson, content_type: e.target.value })}>
            <option value="text">text</option>
            <option value="pdf">pdf</option>
            <option value="video">video</option>
          </select>
          <textarea className="input" placeholder={t("lms.content")} value={lesson.content}
                    onChange={(e) => setLesson({ ...lesson, content: e.target.value })} />
          <input className="input" type="number" placeholder={t("lms.order")} value={lesson.order_index}
                 onChange={(e) => setLesson({ ...lesson, order_index: e.target.value })} />
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setLessonOpen(false)}>{t("common.cancel")}</button>
            <button className="btn-primary">{t("common.create")}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
