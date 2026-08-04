import { useState, useEffect, useCallback } from "react";
import { adminTeacherClasses, TeacherCourseCatalogEntry, TeacherClassInfo, ClassCourseAccessInfo, StudentEnrollmentInfo } from "../api";

export default function SuperAdminCourseFactory() {
  const [catalog, setCatalog] = useState<TeacherCourseCatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expandedClass, setExpandedClass] = useState<number | null>(null);
  const [classCourses, setClassCourses] = useState<Record<number, ClassCourseAccessInfo[]>>({});
  const [classStudents, setClassStudents] = useState<Record<number, StudentEnrollmentInfo[]>>({});

  const loadCatalog = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminTeacherClasses.catalog({ search: search || undefined });
      setCatalog(data.classes);
    } catch (e) {
      console.error("Failed to load teacher catalog", e);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const toggleExpand = async (classId: number) => {
    if (expandedClass === classId) {
      setExpandedClass(null);
      return;
    }
    setExpandedClass(classId);
    if (!classCourses[classId]) {
      try {
        const [courses, students] = await Promise.all([
          adminTeacherClasses.listCourses(classId),
          adminTeacherClasses.listStudents(classId),
        ]);
        setClassCourses((prev) => ({ ...prev, [classId]: courses }));
        setClassStudents((prev) => ({ ...prev, [classId]: students }));
      } catch (e) {
        console.error("Failed to load class details", e);
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-navy">Super Admin Course Factory</h1>
          <p className="text-gray mt-1">
            Browse all teacher-created classes, their assigned courses, and enrolled students.
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by class name, teacher name, or school..."
          className="w-full max-w-md px-4 py-2 border border-gray/20 rounded-xl bg-white text-sm focus:outline-none focus:ring-2 focus:ring-orange/50"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-bold text-navy">{catalog.length}</div>
          <div className="text-sm text-gray mt-1">Teacher Classes</div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-bold text-navy">
            {catalog.reduce((sum, c) => sum + c.courses.length, 0)}
          </div>
          <div className="text-sm text-gray mt-1">Courses Assigned</div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-bold text-navy">
            {catalog.reduce((sum, c) => sum + c.students_count, 0)}
          </div>
          <div className="text-sm text-gray mt-1">Enrolled Students</div>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <div className="text-2xl font-bold text-navy">
            {new Set(catalog.map((c) => c.teacher_id)).size}
          </div>
          <div className="text-sm text-gray mt-1">Active Teachers</div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-orange border-t-transparent rounded-full mx-auto"></div>
          <p className="text-gray mt-3">Loading catalog...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && catalog.length === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-black/5">
          <svg className="w-16 h-16 mx-auto text-gray/40 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-lg font-semibold text-navy mb-1">No teacher classes found</h3>
          <p className="text-gray text-sm">Teachers haven't created any classes yet.</p>
        </div>
      )}

      {/* Catalog List */}
      {!loading && catalog.length > 0 && (
        <div className="space-y-4">
          {catalog.map((entry) => (
            <div key={entry.class_id} className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
              {/* Class Header */}
              <button
                onClick={() => toggleExpand(entry.class_id)}
                className="w-full flex items-center justify-between p-5 hover:bg-cream/50 transition-colors text-start"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-navy">{entry.class_name}</h3>
                    {entry.class_code && (
                      <span className="px-2 py-0.5 text-xs font-mono bg-gray/10 text-gray rounded-md">
                        {entry.class_code}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray">
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      {entry.teacher_name || `Teacher #${entry.teacher_id}`}
                    </span>
                    {entry.school_name && (
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                        {entry.school_name}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 me-4">
                  <div className="text-center">
                    <div className="text-sm font-semibold text-navy">{entry.courses.length}</div>
                    <div className="text-xs text-gray">Courses</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-navy">{entry.students_count}</div>
                    <div className="text-xs text-gray">Students</div>
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 text-gray transition-transform ${expandedClass === entry.class_id ? "rotate-180" : ""}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Expanded Details */}
              {expandedClass === entry.class_id && (
                <div className="border-t border-black/5 p-5 space-y-6">
                  {/* Courses */}
                  <div>
                    <h4 className="text-sm font-semibold text-navy mb-3">
                      Assigned Courses ({classCourses[entry.class_id]?.length || 0})
                    </h4>
                    {classCourses[entry.class_id]?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {classCourses[entry.class_id].map((ca) => (
                          <span
                            key={ca.id}
                            className="px-3 py-1.5 bg-orange/10 text-orange-dark text-sm rounded-lg font-medium"
                          >
                            {ca.course_title || `Course #${ca.course_id}`}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray/60 italic">No courses assigned yet.</p>
                    )}
                  </div>

                  {/* Students */}
                  <div>
                    <h4 className="text-sm font-semibold text-navy mb-3">
                      Enrolled Students ({classStudents[entry.class_id]?.length || 0})
                    </h4>
                    {classStudents[entry.class_id]?.length ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-start text-gray text-xs uppercase tracking-wider border-b border-black/5">
                              <th className="pb-2 font-medium">Name</th>
                              <th className="pb-2 font-medium">Email</th>
                              <th className="pb-2 font-medium">Enrolled At</th>
                            </tr>
                          </thead>
                          <tbody>
                            {classStudents[entry.class_id].map((s) => (
                              <tr key={s.id} className="border-b border-black/5 last:border-0">
                                <td className="py-2 text-navy font-medium">
                                  {s.student_name || `Student #${s.student_id}`}
                                </td>
                                <td className="py-2 text-gray">{s.student_email || "-"}</td>
                                <td className="py-2 text-gray">
                                  {s.enrolled_at ? new Date(s.enrolled_at).toLocaleDateString() : "-"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-sm text-gray/60 italic">No students enrolled yet.</p>
                    )}
                  </div>

                  {/* Metadata */}
                  <div className="text-xs text-gray/50 pt-2 border-t border-black/5">
                    Created {entry.created_at ? new Date(entry.created_at).toLocaleDateString() : "N/A"}
                    {entry.teacher_email && ` · Teacher: ${entry.teacher_email}`}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
