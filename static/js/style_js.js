document.addEventListener('alpine:init', () => {
    Alpine.data('unifiedDashboard', (userRole = 'student', initialUsers = [], initialTimetables = []) => ({

        // ==========================================
        // ១. ការកំណត់ State និងអថេរគោល
        // ==========================================
        role: userRole,
        users: initialUsers,
        departmentRows: [],
        colleges: [],
        departments: [],
        subjects: [],
        classes: [],
        teachers: [],
        teacherSearchQuery: '',
        teacherDepartmentFilter: '',
        teacherSearchQuery: '',
        teacherDepartmentFilter: '',
        teacherSubjectFilter: '',
        teacherStatusFilter: '',
        classNameMap: {
            1: 'M1', 2: 'M2', 3: 'M3', 4: 'M4', 5: 'M5',
            6: 'M6', 7: 'M7', 8: 'M8', 9: 'M9',
            10: 'A1', 11: 'A2', 12: 'A3', 13: 'A4', 14: 'A5',
            15: 'A6', 16: 'A7', 17: 'A8', 18: 'A9',
            19: 'E1', 20: 'E2', 21: 'E3', 22: 'E4', 23: 'E5',
            24: 'E6', 25: 'E7', 26: 'E8', 27: 'E9',
            28: 'SLS'
        },
        // បញ្ជីអាគារសម្រាប់ Dropdown (Array of objects)
        buildings: [
            { id: 1, building_name: 'អាគារ A (Building 1)' },
            { id: 2, building_name: 'អាគារ B (Building 2)' },
            { id: 3, building_name: 'អាគារ C (Building 3)' },
            { id: 4, building_name: 'អាគារ D (Building 4)' },
            { id: 5, building_name: 'អាគារ T (Building 5)' }
        ],
        // Map សម្រាប់ Lookup តាម id (ប្រើជំនួស building_id ចាស់)
        buildingMap: {
            1: 'អាគារ A (Building 1)',
            2: 'អាគារ B (Building 2)',
            3: 'អាគារ C (Building 3)',
            4: 'អាគារ D (Building 4)',
            5: 'អាគារ T (Building 5)'
        },
        adminAttendanceList: [],
        schedules: [],
        scheduleFilter: {
            department_id: '',
            academic_year_id: '',
            building_id: ''
        },
        scheduleViewMode: 'grid',
        rooms: [],
        academic_years: [
            { id: 1, year_name: 'ឆ្នាំទី ១ (Year 1)' },
            { id: 2, year_name: 'ឆ្នាំទី ២ (Year 2)' },
            { id: 3, year_name: 'ឆ្នាំទី ៣ (Year 3)' },
            { id: 4, year_name: 'ឆ្នាំទី ៤ (Year 4)' }
        ],
        sessionSlots: {
            M: ["07:30 AM - 09:00 AM", "09:30 AM - 10:30 AM"],
            A: ["02:30 PM - 04:00 PM", "04:30 PM - 05:30 PM"],
            E: ["06:30 PM - 08:00 PM", "08:30 PM - 09:30 PM"]
        },
        scheduleForm: {
            day_of_week: 'Monday',
            department_id: '',
            academic_year_id: '',
            class_id: '',
            subject_id: '',
            room_id: '',
            start_time: '',
            end_time: '',
            teacher_id: 2
        },
        editingId: null,
        isScheduleModalOpen: false,
        adminAttFilter: {
            date: '',
            class_id: ''
        },
        admin_edit_att_modal: false,
        timetables: initialTimetables,
        searchQuery: '',
        collegeFilter: '',
        departmentFilter: '',
        classOrderBy: 'class_name',
        classOrderDir: 'asc',

        // អថេរសម្រាប់ Modal បន្ថែមដេប៉ាតឺម៉ង់
        add_department: false, 
        deptForm: { college_id: '', name: '' }, 
        edit_department: false,
        update_department: false, // សម្រាប់បើក/បិទ Modal កែប្រែ
        // អថេរសម្រាប់ My Profile
        editingProfile: false,
        profileForm: { name: '', email: '', phone: '', address: '' },
        isClassModalOpen: false,
        classModalMode: 'add',
        classForm: {
            id: '',
            class_name: '',
            session_type: '',
            department_id: '',
            academic_year_id: '',
            building_id: '',
            room_id: ''
        }, // សម្រាប់ Manage Classes
        editAttForm: {id: '', student_name: '', subject_name: '', status: '', remarks: ''}, // សម្រាប់កែប្រែវត្តមាន
        reportSummary: { students: 0, teachers: 0, classes: 0 },
        teacherForm: { id: '', user_id: '', teacher_name: '', teacher_code: '', department_id: '', subject_id: '' },
        availableUsers: [],
        // អថេរសម្រាប់ User & Student Modals
        isUserModalOpen: false,
        isStudentModalOpen: false,
        modalMode: 'add',
        userFormError: '',
        userForm: { 
            id: '', name: '', email: '', role: 'Student', status: 'Active',
            phone: '', address: '', dob: '',
            idNumber: '', department: '', year: '',
            class_id: '', gender: 'Male', college: '', generation_id: ''
        },

        // អថេរសម្រាប់ IT Support & Chat
        isSubmitting: false,
        ticketForm: { subject: '', category: 'System Bug', priority: 'Medium', description: '' },
        add_subject_modal: false,
        update_subject_modal: false,
        add_class_modal: false,
        update_class_modal: false,
        add_teacher_modal: false,
        edit_teacher_modal: false,
        subjectForm: { id: '', subject_name: '', department_id: '', year_id: '', semester: '1', credits: 3 },
        isChatOpen: false,
        chatInput: '',
        chatHistory: [
            { sender: 'bot', text: 'សួស្តី! ខ្ញុំគឺ UniBot។ តើថ្ងៃនេះមានអ្វីឱ្យខ្ញុំជួយដែរឬទេ?' }
        ],

        // អថេរសម្រាប់ Teacher Attendance
        attendanceForm: {
            date: new Date().toISOString().split('T')[0],
            course: '',
            records: {} 
        },

        activeTab: (() => {
            if (userRole === 'admin') return 'system_overview';
            if (userRole === 'teacher') return 'statistics';
            return 'student_overview';
        })(),

        async init() {
            try {
                const [colRes, depRes, clsRes, yearRes] = await Promise.all([
                    fetch('/api/admin/colleges').catch(() => null),
                    fetch('/api/admin/departments').catch(() => null),
                    fetch('/api/admin/classes').catch(() => null),
                    fetch('/api/admin/academic_years').catch(() => null)
                ]);

                if (colRes && colRes.ok) {
                    const colData = await colRes.json();
                    if (colData.status === 'success') this.colleges = colData.data || [];
                }

                if (depRes && depRes.ok) {
                    const depData = await depRes.json();
                    if (depData.status === 'success') this.departments = depData.data || [];
                }

                if (clsRes && clsRes.ok) {
                    const clsData = await clsRes.json();
                    if (clsData.status === 'success') this.classes = clsData.data || [];
                }

                if (yearRes && yearRes.ok) {
                    const yearData = await yearRes.json();
                    if (yearData.status === 'success') this.academic_years = yearData.data || [];
                }

                // Ensure subject dropdown data exists for ManageTeacher + EditTeacher modal
                await this.fetchSubjectsSafe();

            } catch (error) {
                console.error('init error:', error);
            }
        },

        async fetchSubjectsSafe() {
            try {
                const res = await fetch('/api/admin/subjects', { method: 'GET' });
                if (!res.ok) return;

                const payload = await res.json();
                if (payload?.status !== 'success') return;

                const rows = Array.isArray(payload.data) ? payload.data : [];
                this.subjects = rows.map(s => ({
                    id: s.id,
                    subject_name: s.subject_name || s.name || '',
                    department_id: s.department_id ?? '',
                    year_id: s.year_id ?? '',
                    semester: s.semester ?? ''
                }));
            } catch (err) {
                console.error('fetchSubjectsSafe error:', err);
            }
        },

        // ==========================================
        // ២. ការស្វែងរក និងត្រងទិន្នន័យ (Search Filter)
        // ==========================================
        get departmentOptions() {
            const rows = Array.isArray(this.departmentRows) ? this.departmentRows : [];
            const selectedCollege = String(this.collegeFilter || '').trim();

            const filtered = selectedCollege
                ? rows.filter(r => String(r.college_id || '') === selectedCollege)
                : rows;

            const seen = new Set();
            const unique = [];

            for (const r of filtered) {
                const id = String(r.department_id || r.id || '');
                if (!id || seen.has(id)) continue;
                seen.add(id);
                unique.push({
                    id,
                    department_name: r.department_name || ''
                });
            }

            return unique.sort((a, b) =>
                String(a.department_name).localeCompare(String(b.department_name), undefined, {
                    sensitivity: 'base',
                    numeric: true
                })
            );
        },

        get filteredUsers() {
            const source = this.activeTab === 'admin_department' ? this.departmentRows : this.users;
            const list = Array.isArray(source) ? source : [];
            const q = String(this.searchQuery || '').trim().toLowerCase();

            if (this.activeTab === 'admin_department') {
                let rows = [...list];

                const selectedCollege = String(this.collegeFilter || '').trim();
                const selectedDepartment = String(this.departmentFilter || '').trim();

                if (selectedCollege) {
                    rows = rows.filter(r => String(r.college_id || '') === selectedCollege);
                }

                if (selectedDepartment) {
                    rows = rows.filter(r => String(r.department_id || r.id || '') === selectedDepartment);
                }

                if (!q) return rows;

                return rows.filter(r => {
                    const deptName = String(r.department_name || '').toLowerCase();
                    const collegeName = String(r.college_name || '').toLowerCase();
                    return deptName.includes(q) || collegeName.includes(q);
                });
            }

            if (!q) return list;

            return list.filter(user => {
                const name = String(user.student_name || user.name || '').toLowerCase();
                const email = String(user.email || '').toLowerCase();
                const idNumber = String(user.id_number || user.idNumber || '').toLowerCase();
                const dept = String(user.department_name || '').toLowerCase();
                const college = String(user.college_name || '').toLowerCase();
                return name.includes(q) || email.includes(q) || idNumber.includes(q) || dept.includes(q) || college.includes(q);
            });
        },

        get filteredSortedStudents() {
            const source = Array.isArray(this.filteredUsers) ? this.filteredUsers : [];
            const classById = new Map((Array.isArray(this.classes) ? this.classes : []).map(c => [String(c.id), c]));

            let list = source.filter(u => String(u?.role || '').toLowerCase() === 'student');

            if (String(this.classFilter?.year_id || '').trim() !== '') {
                const selectedYear = String(this.classFilter.year_id);
                list = list.filter(u => {
                    const cls = classById.get(String(u.class_id || '')) || {};
                    const yearId = String(u.academic_year_id || u.year || cls.academic_year_id || '');
                    return yearId === selectedYear;
                });
            }

            if (String(this.classFilter?.building_id || '').trim() !== '') {
                const selectedBuilding = String(this.classFilter.building_id);
                list = list.filter(u => {
                    const cls = classById.get(String(u.class_id || '')) || {};
                    const buildingId = String(u.building_id || cls.building_id || '');
                    return buildingId === selectedBuilding;
                });
            }

            const dir = this.classOrderDir === 'desc' ? -1 : 1;
            const field = this.classOrderBy || 'class_name';

            return [...list].sort((a, b) => {
                const classA = classById.get(String(a.class_id || '')) || {};
                const classB = classById.get(String(b.class_id || '')) || {};

                let av = '';
                let bv = '';

                if (field === 'class_name') {
                    av = a.class_name || classA.class_name || '';
                    bv = b.class_name || classB.class_name || '';
                } else if (field === 'department_name') {
                    av = a.department_name || '';
                    bv = b.department_name || '';
                } else if (field === 'academic_year') {
                    av = a.year_name || a.academic_year_name || '';
                    bv = b.year_name || b.academic_year_name || '';
                } else if (field === 'student_count') {
                    av = 1;
                    bv = 1;
                } else {
                    av = a[field] ?? '';
                    bv = b[field] ?? '';
                }

                const an = Number(av);
                const bn = Number(bv);
                const bothNumeric = !Number.isNaN(an) && !Number.isNaN(bn) && av !== '' && bv !== '';
                if (bothNumeric) return (an - bn) * dir;

                return String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' }) * dir;
            });
        },

        get timeSlots() {
            const selectedClass = (this.classes || []).find(c => String(c.id) === String(this.scheduleForm.class_id));
            if (selectedClass && selectedClass.session_type) {
                return this.sessionSlots[selectedClass.session_type] || [];
            }

            // Fallback: show all slots so user can still choose start/end time before selecting class.
            return Object.values(this.sessionSlots || {}).flat();
        },

        get classOptions() {
            return (this.classes || []).map(cls => ({
                ...cls,
                // Keep DB-provided class names so each academic year shows correctly.
                class_name: cls.class_name || this.classNameMap[Number(cls.id)] || ''
            }));
        },

        get filteredClassOptions() {
            const dept = String(this.scheduleForm?.department_id || '').trim();
            const year = String(this.scheduleForm?.academic_year_id || '').trim();

            return this.classOptions.filter(cls => {
                const clsDept = String(cls.department_id || '').trim();
                const clsYear = String(cls.academic_year_id || '').trim();
                const depOk = !dept || dept === clsDept;
                const yearOk = !year || year === clsYear;
                return depOk && yearOk;
            });
        },

        get filteredSubjects() {
            const source = Array.isArray(this.subjects) ? this.subjects : [];
            const selectedDept = String(this.scheduleForm?.department_id || '').trim();
            const selectedYear = String(this.scheduleForm?.academic_year_id || '').trim();

            let result = source.filter(sub => {
                const subDept = String(sub.department_id || '').trim();
                const subYear = String(sub.year_id || '').trim();
                const deptOk = !selectedDept || subDept === selectedDept;
                const yearOk = !selectedYear || subYear === selectedYear;
                return deptOk && yearOk;
            });

            const q = (this.searchQuery || '').trim().toLowerCase();
            if (q) {
                result = result.filter(sub => {
                    const name = String(sub.subject_name || '').toLowerCase();
                    const dept = String(sub.department_name || '').toLowerCase();
                    const year = String(sub.year_name || '').toLowerCase();
                    return name.includes(q) || dept.includes(q) || year.includes(q);
                });
            }

            return result.sort((a, b) =>
                String(a.subject_name || '').localeCompare(String(b.subject_name || ''))
            );
        },

        get filteredScheduleTeachers() {
            const source = Array.isArray(this.teachers) ? this.teachers : [];
            const selectedDept = String(this.scheduleForm?.department_id || '').trim();
            const selectedSubjectId = String(this.scheduleForm?.subject_id || '').trim();

            const selectedSubject = (this.subjects || []).find(
                s => String(s.id || '') === selectedSubjectId
            );
            const selectedSubjectName = String(selectedSubject?.subject_name || '').trim().toLowerCase();

            let result = source.filter(t => {
                const teacherDept = String(t.department_id || '').trim();
                return !selectedDept || teacherDept === selectedDept;
            });

            if (selectedSubjectId) {
                result = result.filter(t => {
                    const teacherSubjectId = String(t.subject_id || '').trim();
                    const teacherSubjectName = String(t.subject_teach || '').trim().toLowerCase();
                    return (
                        (teacherSubjectId && teacherSubjectId === selectedSubjectId)
                        || (selectedSubjectName && teacherSubjectName === selectedSubjectName)
                    );
                });
            }

            return result.sort((a, b) =>
                String(a.teacher_name || '').localeCompare(String(b.teacher_name || ''))
            );
        },

        get filteredSchedulesList() {
            const source = Array.isArray(this.schedules) ? this.schedules : [];
            const dep = String(this.scheduleFilter?.department_id || '').trim();
            const year = String(this.scheduleFilter?.academic_year_id || '').trim();
            const building = String(this.scheduleFilter?.building_id || '').trim();

            return source.filter(item => {
                const itemDep = String(item.department_id || '').trim();
                const itemYear = String(item.academic_year_id || '').trim();
                const itemBuilding = String(item.building_id || '').trim();

                const depOk = !dep || dep === itemDep;
                const yearOk = !year || year === itemYear;
                const buildingOk = !building || building === itemBuilding;
                return depOk && yearOk && buildingOk;
            });
        },

        theme: {
            bg: userRole === 'admin' ? 'bg-blue-600' : (userRole === 'teacher' ? 'bg-emerald-600' : 'bg-violet-600'),
            text: userRole === 'admin' ? 'text-blue-600' : (userRole === 'teacher' ? 'text-emerald-600' : 'text-violet-600'),
            activeClass: userRole === 'admin' ? 'bg-blue-50 text-blue-600' : (userRole === 'teacher' ? 'bg-emerald-50 text-emerald-600' : 'bg-violet-50 text-violet-600'),
            inactiveClass: 'text-slate-500 hover:bg-slate-50 hover:text-slate-700',
            ring: userRole === 'admin' ? 'focus:ring-blue-600' : (userRole === 'teacher' ? 'focus:ring-emerald-600' : 'focus:ring-violet-600'),
            border: userRole === 'admin' ? 'border-blue-200 text-blue-600' : (userRole === 'teacher' ? 'border-emerald-200 text-emerald-600' : 'border-violet-200 text-violet-600'),
        },

        toast: { visible: false, message: '', type: 'success' },
        
        // ==========================================
        // ៣. មុខងារទូទៅ (Tab & Toast)
        // ==========================================
        switchTab(tab) { 
            this.activeTab = tab;
            this.editingProfile = false;
            this.searchQuery = '';

            switch(tab) {
                case 'profile': this.fetchProfile(); break;
                case 'admin_department': this.fetchUserView(); break;
                case 'admin_subject': this.fetchSubjects(); break;
                case 'admin_attendance':
                    this.fetchClasses();
                    this.fetchAdminAttendance();
                    break;
                // បន្ថែមមុខងារ Fetch ផ្សេងៗនៅទីនេះពេលលោកអ្នកសរសេររួច
                case 'chat': this.fetchChat(); break;
                case 'statistics': this.fetchStatistics(); break;
                case 'system_overview': this.fetchSystemOverview(); break;
                case 'student_overview': this.fetchStudentOverview(); break;
                case 'admin_class': this.fetchClasses(); break;
                case 'admin_users': this.fetchUsers(); break;
                case 'admin_edit_user': this.fetchUsers(); break;
                case 'admin_students': this.fetchStudents(); break;
                case 'edit_student': this.fetchStudents(); break;
                case 'admin_report':
                    // Backward compatibility for older template keys.
                    this.activeTab = 'admin_reports';
                    this.fetchReports();
                    break;
                case 'admin_reports':
                    this.fetchReports();
                    break;
                case 'admin_schedule':
                    this.fetchSchedules();
                    break;
                case 'admin_teacher':
                    this.fetchTeachers();
                    break;
            }
        },

        // មុខងារទាញទិន្នន័យសង្ខេបសម្រាប់ផ្ទាំង Report
        async fetchReports() {
            try {
                const response = await fetch('/api/reports/summary');
                const result = await response.json();

                if (response.ok && result.status === 'success' && result.data) {
                    this.reportSummary = {
                        students: Number(result.data.students || 0),
                        teachers: Number(result.data.teachers || 0),
                        classes: Number(result.data.classes || 0)
                    };
                }
            } catch (e) {
                console.error('Fetch Error:', e);
            }
        },

        // មុខងារនេះត្រូវហៅពេលចុចប៊ូតុង Edit ក្នុងតារាង: @click="openEditDeptModal(item)"
        openEditDeptModal(item) {
            this.deptForm = {
                id: item.department_id,        // ចាប់យក ID របស់ដេប៉ាតឺម៉ង់សម្រាប់បញ្ជូនទៅ Python
                college_id: item.college_id,   // សម្រាប់ឱ្យ Select Box លោតយកមហាវិទ្យាល័យដើម
                name: item.department_name     // សម្រាប់បំពេញឈ្មោះដេប៉ាតឺម៉ង់ចូលក្នុង Input 
            };
            this.update_department = true; // បើកផ្ទាំង Modal កែប្រែនេះឡើង
        },
        openUpdateDeptModal(user) {
            // ចាប់យកទិន្នន័យចាស់មកបង្ហាញក្នុង Form
            this.deptForm = {
                id: user.department_id,      // ឈ្មោះ Column ID ពី SQL View
                college_id: user.college_id, // ឈ្មោះ Column College ID ពី SQL View
                name: user.department_name   // ឈ្មោះដេប៉ាតឺម៉ង់
            };
            this.update_department = true; // បើក Modal
        },

        async updateDepartment() {
            if (!this.deptForm.college_id || !this.deptForm.name) {
                this.showToast("សូមបំពេញព័ត៌មានឱ្យគ្រប់!", "error");
                return;
            }

            try {
                const response = await fetch('/update_department', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.deptForm)
                });
                const result = await response.json();

                if (result.status === 'success') {
                    this.showToast(result.message, 'success');
                    this.edit_department = false; // បិទ Modal
                    this.deptForm = { id: '', college_id: '', name: '' }; // Reset Form
                    this.fetchUserView(); // Refresh តារាង
                } else {
                    this.showToast(result.message, 'error');
                }
            } catch (error) {
                this.showToast("មានបញ្ហាបច្ចេកទេសក្នុងការកែប្រែ!", "error");
            }
        },
        showToast(msg, type = 'success') {
            this.toast.message = msg;
            this.toast.type = type;
            this.toast.visible = true;
            setTimeout(() => { this.toast.visible = false; }, 3000);
        },

        // ==========================================
        // ៤. មុខងារគ្រប់គ្រងរចនាសម្ព័ន្ធ (Department View)
        // ==========================================
        async fetchUserView() {
            try {
                const response = await fetch('/manageDepartment');
                const result = await response.json();
                if (result.status === 'success') {
                    this.departmentRows = Array.isArray(result.users) ? result.users : [];
                } else {
                    this.departmentRows = [];
                    this.showToast(result.message, 'error');
                }
            } catch (error) {
                this.departmentRows = [];
                console.error("Error fetching view:", error);
            }
        },

        normalizeUsers(list) {
            const source = Array.isArray(list) ? list : [];
            const seen = new Set();

            return source.reduce((acc, user) => {
                const u = user || {};
                const id = u.id ?? u.user_id ?? '';
                const email = String(u.email || '').toLowerCase();
                const key = `${id}::${email}::${String(u.name || '')}`;
                if (seen.has(key)) return acc;
                seen.add(key);

                acc.push({
                    ...u,
                    id,
                    id_number: u.id_number || u.idNumber || ''
                });
                return acc;
            }, []);
        },

        async fetchUsers() {
            try {
                const response = await fetch('/api/admin/users');
                if (response.ok) {
                    const result = await response.json();
                    if (result.status === 'success') {
                        this.users = this.normalizeUsers(result.data);
                        return;
                    }
                }
            } catch (error) {
                console.warn('fetchUsers fallback to initial users:', error);
            }

            // Fallback when API is unavailable: keep current injected users but normalize.
            this.users = this.normalizeUsers(this.users);
        },

        async fetchStudents() {
            try {
                const response = await fetch('/api/admin/student');
                if (response.ok) {
                    const result = await response.json();
                    if (result.status === 'success') {
                        this.users = this.normalizeUsers(result.data);
                        return;
                    }
                }
            } catch (error) {
                console.warn('fetchStudents fallback to current users:', error);
            }

            // Fallback when API is unavailable: keep current injected users but normalize.
            this.users = this.normalizeUsers(this.users).filter(
                user => String(user.role || '').toLowerCase() === 'student'
            );
        },
        

        async fetchAdminAttendance() {
            try {
                const response = await fetch('/manageAttendance');
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    let records = Array.isArray(result.attendance) ? result.attendance : [];

                    // Filter by selected date/class on frontend so existing API remains simple.
                    if (this.adminAttFilter.date) {
                        records = records.filter(att => {
                            const raw = att.attendance_date;
                            if (!raw) return false;
                            const d = new Date(raw);
                            if (Number.isNaN(d.getTime())) return false;
                            const yyyy = d.getFullYear();
                            const mm = String(d.getMonth() + 1).padStart(2, '0');
                            const dd = String(d.getDate()).padStart(2, '0');
                            return `${yyyy}-${mm}-${dd}` === this.adminAttFilter.date;
                        });
                    }

                    if (this.adminAttFilter.class_id) {
                        const selected = this.classes.find(cls => String(cls.id) === String(this.adminAttFilter.class_id));
                        const selectedClassName = selected ? selected.class_name : null;

                        if (selectedClassName) {
                            records = records.filter(att => String(att.class_name || '') === String(selectedClassName));
                        }
                    }

                    this.adminAttendanceList = records;
                } else {
                    this.adminAttendanceList = [];
                    this.showToast(result.message || 'មិនអាចទាញយកទិន្នន័យវត្តមានបានទេ', 'error');
                }
            } catch (error) {
                this.adminAttendanceList = [];
                this.showToast('មិនអាចភ្ជាប់ទៅម៉ាស៊ីនមេបានទេ', 'error');
                console.error('Error fetching attendance:', error);
            }
        },

        formatDate(value) {
            if (!value) return '-';
            const d = new Date(value);
            if (Number.isNaN(d.getTime())) return String(value);
            const yyyy = d.getFullYear();
            const mm = String(d.getMonth() + 1).padStart(2, '0');
            const dd = String(d.getDate()).padStart(2, '0');
            return `${yyyy}-${mm}-${dd}`;
        },

        // មុខងារគោលសម្រាប់ទាញយករបាយការណ៍
        async generateReport(type, format) {
            this.showToast('កំពុងរៀបចំទិន្នន័យ...', 'success');

            try {
                const response = await fetch(`/api/reports/get_all_data?type=${encodeURIComponent(type)}`);
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    const data = Array.isArray(result.data) ? result.data : [];
                    if (data.length === 0) {
                        this.showToast('មិនមានទិន្នន័យទេ!', 'error');
                        return;
                    }

                    if (format === 'excel') {
                        this.downloadAsExcel(data, type);
                    } else if (format === 'word') {
                        this.downloadAsWord(data, type);
                    }
                } else {
                    this.showToast(result.message || 'មានបញ្ហាក្នុងការទាញទិន្នន័យ!', 'error');
                }
            } catch (error) {
                this.showToast('មិនអាចភ្ជាប់ទៅម៉ាស៊ីនមេបានទេ', 'error');
            }
        },

        // មុខងារបំប្លែងទៅជា Excel (CSV)
        downloadAsExcel(data, type) {
            const headers = Object.keys(data[0]);
            let csvContent = headers.join(',') + '\n';

            data.forEach(row => {
                const values = headers.map(header => {
                    const val = row[header] === null || row[header] === undefined ? '' : String(row[header]);
                    return `"${val.replace(/"/g, '""')}"`;
                });
                csvContent += values.join(',') + '\n';
            });

            const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.download = `Report_${type}_${new Date().toISOString().slice(0, 10)}.csv`;
            link.click();
            URL.revokeObjectURL(url);
        },

        // មុខងារបំប្លែងទៅជា Word (DOC)
        downloadAsWord(data, type) {
            const headers = Object.keys(data[0]);

            let tableHTML = "<table border=\"1\" style=\"border-collapse: collapse; width: 100%;\">";
            tableHTML += `<tr style="background-color: #f2f2f2;">${headers.map(h => `<th style="padding: 8px;">${h}</th>`).join('')}</tr>`;

            data.forEach(row => {
                tableHTML += `<tr>${headers.map(h => `<td style="padding: 8px;">${row[h] ?? ''}</td>`).join('')}</tr>`;
            });
            tableHTML += '</table>';

            const header = `<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Report</title></head><body><h2 style="text-align: center;">របាយការណ៍សរុប - ${String(type).toUpperCase()}</h2>`;
            const footer = '</body></html>';
            const fullHTML = header + tableHTML + footer;

            const blob = new Blob(['\ufeff', fullHTML], { type: 'application/msword' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.download = `Report_${type}_${new Date().toISOString().slice(0, 10)}.doc`;
            link.click();
            URL.revokeObjectURL(url);
        },

        // មុខងារទាញយករបាយការណ៍ជាឯកសារ Excel (CSV)
        exportToExcel() {
            // ១. ពិនិត្យមើលថាតើមានទិន្នន័យឬទេ
            if (!Array.isArray(this.adminAttendanceList) || this.adminAttendanceList.length === 0) {
                this.showToast('មិនមានទិន្នន័យសម្រាប់ទាញយកទេ!', 'error');
                return;
            }

            // ២. រៀបចំចំណងជើងក្បាលជួរឈរ (Headers)
            let csvContent = 'ថ្ងៃខែឆ្នាំ,ឈ្មោះសិស្ស,ថ្នាក់រៀន,មុខវិជ្ជា,កត់ដោយ(គ្រូ),ស្ថានភាព,មូលហេតុ\n';

            // ៣. បញ្ចូលទិន្នន័យជួរនីមួយៗ (Data rows)
            this.adminAttendanceList.forEach(att => {
                const date = this.formatDate(att.attendance_date);
                const student = att.student_name || '';
                const className = att.class_name || '';
                const subject = att.subject_name || '';
                const teacher = att.teacher_name || '';

                // បំប្លែងស្ថានភាពជាភាសាខ្មែរ
                const status = att.status === 'Present' ? 'វត្តមាន' :
                    (att.status === 'Absent' ? 'អវត្តមាន' :
                    (att.status === 'Late' ? 'យឺត' : 'ច្បាប់'));

                const remarks = att.remarks || '';

                // ដាក់សញ្ញា "" ព័ទ្ធជុំវិញ text ដើម្បីការពារបញ្ហា comma/newline ក្នុងតម្លៃ
                const escapeCsv = (v) => String(v).replace(/"/g, '""').replace(/\r?\n/g, ' ');
                const row = `"${escapeCsv(date)}","${escapeCsv(student)}","${escapeCsv(className)}","${escapeCsv(subject)}","${escapeCsv(teacher)}","${escapeCsv(status)}","${escapeCsv(remarks)}"`;
                csvContent += row + '\n';
            });

            // ៤. បង្កើត File និងទាញយកដោយស្វ័យប្រវត្តិ
            // ប្រើ \uFEFF (UTF-8 BOM) ដើម្បីឱ្យ Excel ស្គាល់អក្សរខ្មែរបានត្រឹមត្រូវ
            const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            const fileName = `របាយការណ៍វត្តមាន_${this.adminAttFilter.date || 'សរុប'}.csv`;

            link.setAttribute('href', url);
            link.setAttribute('download', fileName);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            this.showToast('ទាញយកឯកសារ Excel បានជោគជ័យ!', 'success');
        },
        get filteredSubjects() {
            const source = Array.isArray(this.subjects) ? this.subjects : [];
            const selectedDept = String(this.scheduleForm?.department_id || '').trim();
            const selectedYear = String(this.scheduleForm?.academic_year_id || '').trim();

            let result = source.filter(sub => {
                const subDept = String(sub.department_id || '').trim();
                const subYear = String(sub.year_id || '').trim();
                const deptOk = !selectedDept || subDept === selectedDept;
                const yearOk = !selectedYear || subYear === selectedYear;
                return deptOk && yearOk;
            });

            const q = (this.searchQuery || '').trim().toLowerCase();
            if (q) {
                result = result.filter(sub => {
                    const name = String(sub.subject_name || '').toLowerCase();
                    const dept = String(sub.department_name || '').toLowerCase();
                    const year = String(sub.year_name || '').toLowerCase();
                    return name.includes(q) || dept.includes(q) || year.includes(q);
                });
            }

            return result.sort((a, b) =>
                String(a.subject_name || '').localeCompare(String(b.subject_name || ''))
            );
        },

        get filteredClasses() {
            const source = Array.isArray(this.classes) ? this.classes : [];
            if (this.searchQuery.trim() === '') return source;

            const q = this.searchQuery.toLowerCase();

            return source.filter(cls => {
                const className = (cls.class_name || '').toLowerCase();
                const departmentName = (cls.department_name || '').toLowerCase();

                const sessionLabel =
                    cls.session_type === 'M' ? 'វេនព្រឹក' :
                    cls.session_type === 'A' ? 'វេនរសៀល' :
                    cls.session_type === 'E' ? 'វេនយប់' :
                    (cls.session_type === 'SLS' || cls.session_type === 'W') ? 'សៅរ៍-អាទិត្យ' : 'សៅរ៍-អាទិត្យ';

                return (
                    className.includes(q) ||
                    departmentName.includes(q) ||
                    sessionLabel.toLowerCase().includes(q)
                );
            });
        },

        toggleClassSortDirection() {
            this.classOrderDir = this.classOrderDir === 'asc' ? 'desc' : 'asc';
        },

        get sortedFilteredClasses() {
            let list = Array.isArray(this.classes) ? this.classes : [];

            if (this.searchQuery && this.searchQuery.trim() !== '') {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(cls => {
                    const className = (cls.class_name || '').toLowerCase();
                    const deptName = (cls.department_name || '').toLowerCase();
                    const roomName = (cls.room_number || cls.room_name || '').toLowerCase();
                    const session = cls.session_type === 'M' ? 'វេនព្រឹក' :
                                    (cls.session_type === 'A' ? 'វេនរសៀល' :
                                    (cls.session_type === 'E' ? 'វេនយប់' : 'សៅរ៍-អាទិត្យ'));

                    return className.includes(q) ||
                           deptName.includes(q) ||
                           roomName.includes(q) ||
                           session.toLowerCase().includes(q);
                });
            }

            if (this.classFilter.year_id !== '') {
                list = list.filter(cls => String(cls.academic_year_id) === String(this.classFilter.year_id));
            }

            if (this.classFilter.building_id !== '') {
                list = list.filter(cls => String(cls.building_id) === String(this.classFilter.building_id));
            }

            const field = this.classOrderBy || 'class_name';
            const dir = this.classOrderDir === 'desc' ? -1 : 1;

            return list.sort((a, b) => {
                let av = a[field] ?? '';
                let bv = b[field] ?? '';

                if (field === 'academic_year' || field === 'year_name') {
                    av = a.year_name || a.academic_year || '';
                    bv = b.year_name || b.academic_year || '';
                }

                const an = Number(av);
                const bn = Number(bv);
                const bothNumeric = !Number.isNaN(an) && !Number.isNaN(bn) && av !== '' && bv !== '';
                if (bothNumeric) {
                    return (an - bn) * dir;
                }

                return String(av).localeCompare(String(bv), undefined, {
                    numeric: true,
                    sensitivity: 'base'
                }) * dir;
            });
        },

        async fetchSubjects() {
            try {
                const response = await fetch('/manageSubjects');
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    this.subjects = Array.isArray(result.subjects) ? result.subjects : [];
                } else {
                    this.subjects = [];
                    this.showToast(result.message || 'មិនអាចទាញយកបញ្ជីមុខវិជ្ជាបានទេ', 'error');
                }
            } catch (error) {
                this.subjects = [];
                this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
            }
        },

        // ៣. កែប្រែមុខងារពេលបើកផ្ទាំង Edit
        openEditSubjectModal(sub) {
            this.subjectForm = {
                id: sub.id,
                subject_name: sub.subject_name,
                department_id: sub.department_id,
                year_id: sub.year_id,
                semester: sub.semester.toString(), // បំប្លែងទៅជា Text សម្រាប់ Select box
                credits: sub.credits
            };
            this.update_subject_modal = true;
        },
        async saveSubject() {
    // ១. ត្រួតពិនិត្យមើលទិន្នន័យ
    if (!this.subjectForm.subject_name || !this.subjectForm.department_id || !this.subjectForm.year_id) {
        this.showToast('សូមបំពេញព័ត៌មានមុខវិជ្ជាឱ្យគ្រប់!', 'error');
        return;
    }

    // ២. 🌟 ចំណុចសំខាន់៖ ឆែកមើលថាតើកំពុង Update ឬ Add ថ្មី?
    // ប្រសិនបើ subjectForm.id មានតម្លៃ នោះមានន័យថាវាជាការ Update
    const isUpdate = this.subjectForm.id !== '' && this.subjectForm.id !== null;
    
    // កំណត់គោលដៅបញ្ជូនទិន្នន័យទៅកាន់ Python ឱ្យត្រូវ
    const endpoint = isUpdate ? '/update_subject' : '/add_subject';

    // ៣. 🌟 ចំណុចសំខាន់៖ បញ្ចូល id ទៅក្នុង Payload
    const payload = {
        id: this.subjectForm.id, // ត្រូវតែមានដើម្បីឱ្យ Python ដឹងថាត្រូវកែប្រែជួរមួយណា
        name: this.subjectForm.subject_name,
        credits: this.subjectForm.credits || 3,
        semester: this.subjectForm.semester || '1',
        department_id: this.subjectForm.department_id,
        year_id: this.subjectForm.year_id
    };

    try {
        // បញ្ជូនទិន្នន័យទៅកាន់ endpoint ដែលបានកំណត់ខាងលើ
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // បង្ហាញសារខុសគ្នាទៅតាមសកម្មភាព
            this.showToast(result.message || (isUpdate ? 'កែប្រែមុខវិជ្ជាជោគជ័យ!' : 'បន្ថែមមុខវិជ្ជាជោគជ័យ!'), 'success');
            
            // បិទ Modal ទាំងពីរ (ទោះបើកមួយណាក៏បិទដែរ)
            this.add_subject_modal = false;
            this.update_subject_modal = false;
            
            // សម្អាត Form ឱ្យទទេស្អាតវិញ
            this.subjectForm = { id: '', subject_name: '', department_id: '', year_id: '', semester: '1', credits: 3 };
            
            // Refresh តារាង
            this.fetchSubjects();
        } else {
            this.showToast(result.message || 'មិនអាចដំណើរការបានទេ', 'error');
        }
    } catch (error) {
        this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
    }
},

        async saveDepartment() {
            if (!this.deptForm.college_id || !this.deptForm.name) {
                this.showToast("សូមបំពេញព័ត៌មានឱ្យគ្រប់!", "error");
                return;
            }

            try {
                const response = await fetch('/add_department', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.deptForm)
                });
                const result = await response.json();

                if (result.status === 'success') {
                    this.showToast(result.message, 'success');
                    this.add_department = false; 
                    this.deptForm = { college_id: '', name: '' }; 
                    this.fetchUserView(); // Refresh ភ្លាមៗ
                } else {
                    this.showToast(result.message, 'error');
                }
            } catch (error) {
                this.showToast("មានបញ្ហាបច្ចេកទេស!", "error");
            }
        },

        // ==========================================
        // ៥. ផ្នែកប្រវត្តិរូបផ្ទាល់ខ្លួន (My Profile)
        // ==========================================
        async fetchProfile() {
            try {
                const response = await fetch('/profile', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' }
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data.status !== 'error') {
                        this.profileForm = {
                            name: data.name || '',
                            email: data.email || '',
                            phone: data.phone || '',
                            address: data.address || ''
                        };
                    } else {
                        this.showToast(data.message || 'រកមិនឃើញទិន្នន័យ', 'error');
                    }
                }
            } catch (error) {
                this.showToast('មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេ', 'error');
            }
        },

        async saveProfile() {
            try {
                const response = await fetch('/update_my_profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.profileForm)
                });
                const result = await response.json();
                if (result.status === 'success') {
                    this.showToast('កែប្រែប្រវត្តិរូបបានជោគជ័យ!', 'success');
                    this.editingProfile = false;
                    setTimeout(() => window.location.reload(), 1000); 
                } else {
                    this.showToast(result.message, 'error');
                }
            } catch (error) {
                this.showToast('មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេ', 'error');
            }
        },

        cancelEditProfile() { this.editingProfile = false; },

        // ==========================================
        // ៦. មុខងារគ្រប់គ្រងអ្នកប្រើប្រាស់ និងសិស្ស (User & Student Modals)
        // ==========================================
        defaultUserForm() {
            return {
                id: '',
                role: 'Student',
                status: 'Active',
                name: '',
                gender: 'Male',
                email: '',
                phone: '',
                dob: '',
                address: '',
                idNumber: '',
                college: '',
                department: '',
                year: '',
                class_id: '',
                generation_id: ''
            };
        },

        openUserModal(mode = 'add', payload = null) {
            this.modalMode = mode;
            this.userFormError = '';
            this.setupFormData(mode, payload, null);
            this.isUserModalOpen = true;
        },

        closeUserModal() {
            this.isUserModalOpen = false;
            this.userFormError = '';
        },

        openStudentModal(mode = 'add', payload = null) {
            this.modalMode = mode;
            this.userFormError = '';
            this.setupFormData(mode, payload, 'Student');
            this.isStudentModalOpen = true;
        },

        closeStudentModal() {
            this.isStudentModalOpen = false;
            this.userFormError = '';
        },

        setupFormData(mode, payload, forcedRole = null) {
            if (mode === 'edit' && payload) {
                this.userForm = {
                    id: payload.id || payload.user_id || '',
                    role: forcedRole || payload.role || 'Student',
                    status: payload.status || 'Active',
                    name: payload.name || payload.student_name || '',
                    gender: payload.gender || 'Male',
                    email: payload.email || '',
                    phone: payload.phone || '',
                    dob: payload.dob || payload.date_of_birth || '',
                    address: payload.address || '',
                    idNumber: payload.id_number || payload.idNumber || payload.student_code || '',
                    college: payload.college_id || '',
                    department: payload.department_id || payload.department || '',
                    year: payload.academic_year_id || payload.year || '',
                    class_id: payload.class_id || '',
                    generation_id: payload.generation_id || ''
                };
            } else {
                this.userForm = this.defaultUserForm();
                if (forcedRole) this.userForm.role = forcedRole;
                this.generateIdNumber();
            }
        },

        closedataModal() { this.add_department = false; },

        generateIdNumber() {
            if (this.modalMode !== 'add') return;
            const rand = Math.floor(1000 + Math.random() * 9000);
            const prefix = this.userForm.role === 'Student' ? 'STU' : (this.userForm.role === 'Teacher' ? 'TCH' : 'ADM');
            this.userForm.idNumber = `${prefix}-2026-${rand}`;
        },

        generateEmail() {
            if (this.modalMode !== 'add' || !this.userForm.name) return;

            const name = String(this.userForm.name || '').trim().toLowerCase();
            const slug = name
                .replace(/[^\p{L}\p{N}\s._-]/gu, '')
                .replace(/\s+/g, '.')
                .replace(/\.+/g, '.')
                .replace(/^\.|\.$/g, '');

            this.userForm.email = `${slug || 'user'}@hitech.edu`;
        },

        onRoleChange() {
            this.generateIdNumber();
            this.generateEmail();

            if (this.userForm.role === 'Admin') {
                this.userForm.college = '';
                this.userForm.department = '';
                this.userForm.year = '';
                this.userForm.class_id = '';
                this.userForm.generation_id = '';
            } else if (this.userForm.role === 'Teacher') {
                this.userForm.year = '';
                this.userForm.class_id = '';
                this.userForm.generation_id = '';
            }
        },

        validateUserForm() {
            if (!this.userForm.name?.trim()) return 'សូមបញ្ចូលឈ្មោះពេញ!';
            if (!this.userForm.email?.trim()) return 'សូមបញ្ចូលអ៊ីមែល!';
            if (!this.userForm.role?.trim()) return 'សូមជ្រើសរើសតួនាទី!';

            if (this.userForm.role === 'Student' && this.isStudentModalOpen) {
                if (!this.userForm.department) return 'សូមជ្រើសរើសដេប៉ាតឺម៉ង់!';
                if (!this.userForm.year) return 'សូមជ្រើសរើសឆ្នាំសិក្សា!';
            }

            return '';
        },

        async saveUser() {
            this.userFormError = '';

            const error = this.validateUserForm();
            if (error) {
                this.userFormError = error;
                this.showToast(error, 'error');
                return;
            }

            const endpoint = this.modalMode === 'add' ? '/add_user' : `/update_user/${this.userForm.id}`;
            const payload = { ...this.userForm };

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    this.showToast(result.message, 'success');
                    this.closeUserModal();
                    this.closeStudentModal();

                    if (typeof this.fetchUsers === 'function') {
                        await this.fetchUsers();
                    }
                    if (typeof this.fetchStudents === 'function') {
                        await this.fetchStudents();
                    }
                } else {
                    this.userFormError = result.message || 'មានកំហុសកើតឡើងក្នុងការរក្សាទុក!';
                    this.showToast(this.userFormError, 'error');
                }
            } catch (err) {
                console.error('Save User Error:', err);
                this.userFormError = 'មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ';
                this.showToast(this.userFormError, 'error');
            }
        },

        async deleteUser(userId) {
            if (confirm('តើអ្នកពិតជាចង់លុបទិន្នន័យនេះមែនទេ? រាល់ទិន្នន័យពាក់ព័ន្ធនឹងត្រូវលុបចោល!')) {
                try {
                    const response = await fetch(`/delete_user/${userId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const result = await response.json();

                    if (response.ok && result.status === 'success') {
                        this.showToast(result.message, 'success');
                        if (typeof this.fetchUsers === 'function') this.fetchUsers();
                        if (typeof this.fetchStudents === 'function') this.fetchStudents();
                    } else {
                        this.showToast(result.message || 'មិនអាចលុបទិន្នន័យបានទេ', 'error');
                    }
                } catch (error) {
                    this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
                }
            }
        },

        // ==========================================
        // ៧. មុខងារជំនួយផ្សេងៗ (Support & Chatbot)
        // ==========================================
        async submitTicket() {
            this.isSubmitting = true;
            try {
                const response = await fetch('/api/submit_ticket', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.ticketForm)
                });
                const result = await response.json();
                if (response.ok && result.status === 'success') {
                    this.showToast('សំណើរបស់អ្នកត្រូវបានបញ្ជូនជោគជ័យ!', 'success');
                    this.ticketForm = { subject: '', category: 'System Bug', priority: 'Medium', description: '' };
                } else {
                    this.showToast(result.message || 'មានបញ្ហាក្នុងការបញ្ជូនសំណើ!', 'error');
                }
            } catch (error) {
                this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ។', 'error');
            } finally {
                this.isSubmitting = false;
            }
        },

        scrollToBottom() {
            setTimeout(() => {
                const container = document.getElementById('chat-container');
                if (container) container.scrollTop = container.scrollHeight;
            }, 50);
        },

        async sendMessage() {
            if (!this.chatInput.trim()) return;
            const userMsg = this.chatInput.trim();
            this.chatHistory.push({ sender: 'user', text: userMsg });
            this.chatInput = '';
            this.scrollToBottom();

            this.chatHistory.push({ sender: 'bot', text: 'កំពុងវាយអក្សរ...', isTyping: true });
            this.scrollToBottom();

            setTimeout(() => {
                this.chatHistory = this.chatHistory.filter(msg => !msg.isTyping);
                this.chatHistory.push({ sender: 'bot', text: "ខ្ញុំទទួលបានសាររបស់អ្នកហើយ!" });
                this.scrollToBottom();
            }, 1000);
        },

        async submitAttendance() {
            if (!this.attendanceForm.course) {
                this.showToast('សូមបញ្ចូលឈ្មោះមុខវិជ្ជា!', 'error');
                return;
            }
            this.showToast('កត់វត្តមានបានជោគជ័យ!', 'success');
        },
        async deleteDepartment(id) {
            if (!confirm('តើអ្នកពិតជាចង់លុបដេប៉ាតឺម៉ង់នេះមែនទេ? ទិន្នន័យដែលពាក់ព័ន្ធអាចនឹងបាត់បង់!')) return;

            try {
                const response = await fetch(`/delete_department/${id}`, { 
                    method: 'POST', // លោកអ្នកអាចប្រើ DELETE ក៏បាន បើ Python គាំទ្រ
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    this.showToast(result.message, 'success');
                    this.fetchUserView(); // ទាញទិន្នន័យមកបង្ហាញក្នុងតារាងឡើងវិញ (Refresh)
                } else {
                    this.showToast(result.message || 'មិនអាចលុបទិន្នន័យបានទេ', 'error');
                }
            } catch (error) {
                this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
            }
        },

        async deleteSubject(id) {
            try {
                const response = await fetch(`/delete_subject/${id}`, {
                    method: 'POST', // ប្រើ POST ឬ DELETE តាមការគាំទ្ររបស់ Python
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    this.showToast(result.message, 'success');
                    this.fetchSubjects(); // Refresh បញ្ជីមុខវិជ្ជា
                } else {
                    this.showToast(result.message || 'មិនអាចលុបទិន្នន័យបានទេ', 'error');
                }
            } catch (error) {
                this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
            }
        },
            // ==========================================
    // មុខងារគ្រប់គ្រងថ្នាក់រៀន (Classes)
    // ==========================================
    async fetchClasses() {
        try {
            const response = await fetch('/manageClasses');
            const result = await response.json();
            if (response.ok && result.status === 'success') {
                this.classes = Array.isArray(result.classes) ? result.classes : [];
            } else {
                this.classes = [];
                this.showToast(result.message || 'មិនអាចទាញយកបញ្ជីថ្នាក់រៀនបានទេ', 'error');
            }
        } catch (error) {
            this.classes = [];
            this.showToast('មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនមេបានទេ', 'error');
            console.error("Error fetching classes:", error);
        }
    },

    openAddClassModal() {
        this.classModalMode = 'add'; // ត្រូវមានបន្ទាត់នេះទើប save ដើរ
        this.classForm = {
            id: '',
            class_name: '',
            session_type: '',
            department_id: '',
            academic_year_id: '',
            building_id: '',
            room_id: ''
        };

        // Open modal immediately, then refresh dependencies in background.
        this.isClassModalOpen = true;
        this.add_class_modal = true;
        this.update_class_modal = false;

        this.fetchData('/api/admin/academic_years', 'academic_years');
        this.fetchData('/api/admin/rooms', 'rooms');
    },

    async openEditClassModal(cls) {
        this.classModalMode = 'edit';

        try {
            const [yearRes, roomRes] = await Promise.all([
                fetch('/api/admin/academic_years'),
                fetch('/api/admin/rooms')
            ]);

            const yearData = await yearRes.json();
            const roomData = await roomRes.json();

            if (yearRes.ok && yearData.status === 'success') {
                this.academic_years = Array.isArray(yearData.data) ? yearData.data : [];
            }
            if (roomRes.ok && roomData.status === 'success') {
                this.rooms = Array.isArray(roomData.data) ? roomData.data : [];
            }
        } catch (error) {
            console.error('Error loading class modal data:', error);
            this.toast = { visible: true, message: 'មិនអាចទាញយកឆ្នាំសិក្សា ឬ បន្ទប់បានទេ', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
        }

        this.classForm = {
            id: cls.id,
            class_name: cls.class_name || '',
            session_type: cls.session_type || '',
            department_id: cls.department_id || '',
            academic_year_id: cls.academic_year_id || cls.year_id || '',
            building_id: cls.building_id || '',
            room_id: cls.room_id || ''
        };

        this.isClassModalOpen = true;
        this.add_class_modal = false;
        this.update_class_modal = true;
    },

    async saveClass() {
        if (!this.classForm.class_name || !String(this.classForm.class_name).trim()) {
            this.toast = { visible: true, message: 'សូមបញ្ចូលឈ្មោះថ្នាក់រៀន!', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
            return;
        }
        if (!this.classForm.department_id) {
            this.toast = { visible: true, message: 'សូមជ្រើសរើសដេប៉ាតឺម៉ង់!', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
            return;
        }
        if (!this.classForm.session_type) {
            this.toast = { visible: true, message: 'សូមជ្រើសរើសវេនសិក្សា!', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
            return;
        }
        if (!this.classForm.academic_year_id) {
            this.toast = { visible: true, message: 'សូមជ្រើសរើសឆ្នាំសិក្សា!', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
            return;
        }

        const url = this.classModalMode === 'add' ? '/add_class' : '/update_class';
        const payload = {
            ...this.classForm,
            id: this.classForm.id || null,
            class_name: String(this.classForm.class_name || '').trim(),
            department_id: this.classForm.department_id || null,
            session_type: this.classForm.session_type || null,
            academic_year_id: this.classForm.academic_year_id || null,
            building_id: this.classForm.building_id || null,
            room_id: this.classForm.room_id || null
        };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                this.toast = { visible: true, message: result.message, type: 'success' };
                this.isClassModalOpen = false;
                this.add_class_modal = false;
                this.update_class_modal = false;

                await this.fetchData('/manageClasses', 'classes');

                setTimeout(() => this.toast.visible = false, 3000);
            } else {
                this.toast = { visible: true, message: result.message || 'បរាជ័យក្នុងការរក្សាទុក', type: 'error' };
                setTimeout(() => this.toast.visible = false, 4000);
            }
        } catch (error) {
            console.error('Error saving class:', error);
            this.toast = { visible: true, message: 'មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ Server', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
        }
    },

    async deleteClass(id) {
        if (!confirm('តើអ្នកពិតជាចង់លុបថ្នាក់រៀននេះមែនទេ? រាល់ទិន្នន័យសិស្សពាក់ព័ន្ធនឹងត្រូវប៉ះពាល់!')) return;

        try {
            const response = await fetch(`/delete_class/${id}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                this.toast = { visible: true, message: result.message, type: 'success' };
                await this.fetchData('/manageClasses', 'classes');
                setTimeout(() => this.toast.visible = false, 3000);
            } else {
                this.toast = { visible: true, message: result.message || 'មិនអាចលុបបានទេ', type: 'error' };
                setTimeout(() => this.toast.visible = false, 4000);
            }
        } catch (error) {
            console.error('Error deleting class:', error);
            this.toast = { visible: true, message: 'មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ Server', type: 'error' };
            setTimeout(() => this.toast.visible = false, 4000);
        }
    },
    openAdminEditAtt(record) {
        this.editAttForm = {
            id: record.id,
            student_name: record.student_name,
            subject_name: record.subject_name,
            status: record.status,
            remarks: record.remarks || ''
        };
        this.admin_edit_att_modal = true;
    },
    async saveAdminAttendanceEdit() {
        try {
            const response = await fetch('/api/admin/update_attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.editAttForm)
            });
            const result = await response.json();

            if (response.ok && result.status === 'success') {
                this.showToast(result.message, 'success');
                this.admin_edit_att_modal = false;
                if (typeof this.fetchAdminAttendance === 'function') {
                    this.fetchAdminAttendance(); // Refresh តារាងវិញ
                }
            } else {
                this.showToast(result.message || 'មានបញ្ហាក្នុងការរក្សាទុក!', 'error');
            }
        } catch (error) {
            this.showToast('មិនអាចភ្ជាប់ទៅម៉ាស៊ីនមេបានទេ', 'error');
        }
    },

    // Backward compatibility for any old template calls
    async saveAttendanceEdit() {
        return this.saveAdminAttendanceEdit();
    },

    async openAddModal() {
        this.editingId = null;
        this.resetScheduleForm();

        await this.fetchScheduleDependencies();
        this.onClassChange(true);

        this.isScheduleModalOpen = true;
    },

    async editSchedule(item) {
        this.editingId = item.id;
        await this.fetchScheduleDependencies();

        const classId = item.class_id || '';
        const slotRange = this.buildSlotRangeForClass(classId, item.start_time, item.end_time);

        this.scheduleForm = {
            day_of_week: item.day_of_week || 'Monday',
            department_id: item.department_id || '',
            academic_year_id: item.academic_year_id || '',
            class_id: classId,
            subject_id: item.subject_id || '',
            room_id: item.room_id || '',
            // Use slot range so <select> can match option correctly
            start_time: slotRange || '',
            end_time: slotRange || '',
            teacher_id: item.teacher_id || 2
        };

        this.onClassChange(false);
        this.isScheduleModalOpen = true;
    },

    onClassChange(resetTimes = true) {
        const selectedClass = (this.classOptions || []).find(
            c => String(c.id) === String(this.scheduleForm.class_id || '')
        );

        if (selectedClass) {
            if (selectedClass.room_id) {
                this.scheduleForm.room_id = String(selectedClass.room_id);
            }

            if (resetTimes) {
                this.scheduleForm.start_time = '';
                this.scheduleForm.end_time = '';
            }
        }
    },

    buildSlotRangeForClass(classId, startTime, endTime) {
        const selected = (this.classes || []).find(c => String(c.id) === String(classId));
        if (!selected) return '';

        const slots = this.sessionSlots[selected.session_type] || [];
        if (!slots.length) return '';

        const start24 = this.to24hTime(String(startTime || '').slice(0, 8));
        const end24 = this.to24hTime(String(endTime || '').slice(0, 8));

        const found = slots.find(slot => {
            const [s, e] = String(slot).split('-').map(v => v.trim());
            return this.to24hTime(s) === start24 && this.to24hTime(e) === end24;
        });

        return found || '';
    },

    to24hTime(raw) {
        const input = String(raw || '').trim();
        if (!input) return '';

        if (/^\d{2}:\d{2}(:\d{2})?$/.test(input)) {
            return input.length === 5 ? `${input}:00` : input;
        }

        const match = input.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
        if (!match) return input;

        let hour = Number(match[1]);
        const minute = match[2];
        const meridiem = match[3].toUpperCase();

        if (meridiem === 'AM') {
            if (hour === 12) hour = 0;
        } else if (hour !== 12) {
            hour += 12;
        }

        return `${String(hour).padStart(2, '0')}:${minute}:00`;
    },

    async fetchScheduleDependencies() {
        try {
            // ទាញទិន្នន័យចាំបាច់ទាំងអស់ (រួមទាំងគ្រូផង)
            await Promise.all([
                this.fetchData('/api/admin/classes', 'classes'),
                this.fetchData('/api/admin/subjects', 'subjects'),
                this.fetchData('/api/admin/rooms', 'rooms'),
                this.fetchData('/api/admin/departments', 'departments'),
                this.fetchTeachers()
            ]);

            // ទាញឆ្នាំសិក្សា (បើមាន Route ផ្ទាល់)
            const res = await fetch('/api/admin/academic_years');
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                this.academic_years = Array.isArray(result.data) ? result.data : [];
            }
        } catch (e) {
            console.error('Error fetching dependencies:', e);
        }
    },

    async fetchData(url, property) {
        try {
            const res = await fetch(url);
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                this[property] = Array.isArray(result.data) ? result.data : [];
            }
        } catch (e) {
            console.error(`Error fetching ${property}:`, e);
        }
    },

    async fetchRooms() {
        try {
            const res = await fetch('/api/admin/rooms');
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                this.rooms = Array.isArray(result.data) ? result.data : [];
            } else {
                this.rooms = [];
            }
        } catch (e) {
            this.rooms = [];
            console.error('Fetch rooms error:', e);
        }
    },

    async saveSchedule() {
        const url = this.editingId ? `/api/admin/edit_schedule/${this.editingId}` : '/api/admin/add_schedule';

        const selectedSubject = (this.subjects || []).find(
            s => String(s.id) === String(this.scheduleForm.subject_id)
        );
        const selectedClass = (this.classOptions || []).find(
            c => String(c.id) === String(this.scheduleForm.class_id)
        );

        const payload = {
            ...this.scheduleForm,
            department_id: selectedClass?.department_id || this.scheduleForm.department_id || '',
            subject_name: selectedSubject ? selectedSubject.subject_name : '',
            start_time: this.normalizeScheduleTime(this.scheduleForm.start_time, 'start'),
            end_time: this.normalizeScheduleTime(this.scheduleForm.end_time, 'end')
        };

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                if (typeof this.showToast === 'function') {
                    this.showToast(result.message, 'success');
                }
                this.isScheduleModalOpen = false;
                this.fetchSchedules();
            } else if (result && result.message) {
                alert(result.message);
            }
        } catch (e) {
            console.error(e);
        }
    },

    resetScheduleForm() {
        this.scheduleForm = {
            day_of_week: 'Monday',
            department_id: '',
            academic_year_id: '',
            class_id: '',
            subject_id: '',
            room_id: '',
            start_time: '',
            end_time: '',
            teacher_id: 2
        };
    },

    normalizeScheduleTime(value, part) {
        if (!value) return '';

        // If dropdown value is a slot range, extract either start or end time.
        if (String(value).includes('-')) {
            const pieces = String(value).split('-').map(v => v.trim());
            const picked = part === 'end' ? pieces[1] : pieces[0];
            return this.to24hTime(picked);
        }

        return this.to24hTime(String(value));
    },

    to24hTime(raw) {
        const input = String(raw || '').trim();
        if (!input) return '';

        if (/^\d{2}:\d{2}(:\d{2})?$/.test(input)) {
            return input.length === 5 ? `${input}:00` : input;
        }

        const match = input.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
        if (!match) return input;

        let hour = Number(match[1]);
        const minute = match[2];
        const meridiem = match[3].toUpperCase();

        if (meridiem === 'AM') {
            if (hour === 12) hour = 0;
        } else if (hour !== 12) {
            hour += 12;
        }

        return `${String(hour).padStart(2, '0')}:${minute}:00`;
    },

    async fetchSchedules() {
        try {
            // Ensure room metadata is loaded so we can resolve readable room labels.
            if (!Array.isArray(this.rooms) || this.rooms.length === 0) {
                await this.fetchRooms();
            }

            const res = await fetch('/api/admin/schedules');
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                const roomById = new Map(
                    (this.rooms || []).map(r => [String(r.id), r])
                );

                this.schedules = (Array.isArray(result.data) ? result.data : []).map(item => {
                    const linkedRoom = roomById.get(String(item.room_id || '')) || {};
                    const roomNumber = item.room_number || linkedRoom.room_number || '';
                    const roomName = item.room_name || linkedRoom.room_name || '';
                    const buildingId = item.building_id ?? linkedRoom.building_id ?? '';

                    return {
                        ...item,
                        building_id: buildingId,
                        room_number: roomNumber,
                        room_name: roomName,
                        room_display: this.resolveRoomDisplay(roomNumber, roomName)
                    };
                });
            } else {
                this.schedules = [];
                console.error(result.message || 'Failed to load schedules');
            }
        } catch (e) {
            this.schedules = [];
            console.error('Fetch Error:', e);
        }
    },

    resolveRoomDisplay(roomNumber, roomName) {
        const number = String(roomNumber || '').trim();
        const name = String(roomName || '').trim();

        // If room_number looks like plain numeric id, prefer room_name.
        if (number && !/^[0-9]+\.?$/.test(number)) return number;
        if (name) return name;
        if (number) return number;
        return 'N/A';
    },

    filterSchedules() {
        // Filtering is computed by filteredSchedulesList; this method is a trigger hook for template events.
        return this.filteredSchedulesList;
    },

    // កែសម្រួលទ្រង់ទ្រាយម៉ោង (HH:mm)
    formatTime(timeStr) {
        if (!timeStr) return '';
        return String(timeStr).substring(0, 5);
    },

    // លុបកាលវិភាគ
    async deleteSchedule(id) {
        if (!confirm('តើអ្នកពិតជាចង់លុបម៉ោងសិក្សានេះមែនទេ?')) return;

        try {
            const response = await fetch(`/api/admin/delete_schedule/${id}`, { method: 'POST' });
            const result = await response.json();
            if (result.status === 'success') {
                // បង្ហាញ Toast (ប្រសិនបើលោកអ្នកមាន function showToast)
                this.fetchSchedules(); // Update តារាងឡើងវិញ
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error('Delete Error:', error);
        }
    },
    async fetchTeachers() {
        try {
            const res = await fetch('/api/admin/teachers');
            const result = await res.json();
            if (res.ok && result.status === 'success') {
                this.teachers = Array.isArray(result.data) ? result.data : [];
            } else {
                this.teachers = [];
                this.showToast(result.message || 'មិនអាចទាញយកទិន្នន័យគ្រូបានទេ', 'error');
            }
        } catch (e) {
            this.teachers = [];
            console.error('Fetch Teachers Error:', e);
        }
    },
    get filteredTeachers() {
        const query = String(this.teacherSearchQuery || '').toLowerCase();
        const selectedDepartment = String(this.teacherDepartmentFilter || '').trim();
        const source = Array.isArray(this.teachers) ? this.teachers : [];

        let list = source;
        if (selectedDepartment) {
            list = list.filter(t => String(t.department_id || '') === selectedDepartment);
        }

        if (!query) return list;

        return list.filter(t => {
            const name = String(t.teacher_name || '').toLowerCase();
            const code = String(t.teacher_code || '').toLowerCase();
            const dept = String(t.department_name || '').toLowerCase();
            return name.includes(query) || code.includes(query) || dept.includes(query);
        });
    },
    async deleteTeacher(id) {
        // បង្ហាញផ្ទាំងសួរបញ្ជាក់មុននឹងលុប
        if (!confirm('តើអ្នកពិតជាចង់លុបទិន្នន័យគ្រូបង្រៀននេះមែនទេ? ការលុបនេះនឹងមិនប៉ះពាល់ដល់គណនី User ឡើយ។')) {
            return;
        }

        try {
            const res = await fetch(`/api/admin/delete_teacher/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await res.json();
            
            if (result.status === 'success') {
                // បង្ហាញសារជោគជ័យ
                this.showToast(result.message, 'success');
                // Update បញ្ជីគ្រូក្នុងតារាងឡើងវិញ
                this.fetchTeachers();
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (e) {
            console.error('Delete Teacher Error:', e);
            this.showToast('មានបញ្ហាបច្ចេកទេសក្នុងការលុប', 'error');
        }
    },
    async openAddTeacherModal() {
        this.edit_teacher_modal = false;
        this.add_teacher_modal = true;
        this.resetTeacherForm();
        
        try {
            // ទាញយកទិន្នន័យចាំបាច់ទាំងអស់ក្នុងពេលតែមួយ
            const [depRes, subRes, userRes] = await Promise.all([
                fetch('/api/admin/departments'),
                fetch('/api/admin/subjects'),
                fetch('/api/admin/available_teacher_users')
            ]);

            const depData = await depRes.json();
            const subData = await subRes.json();
            const userData = await userRes.json();

            if (depData.status === 'success') this.departments = depData.data;
            if (subData.status === 'success') this.subjects = subData.data;
            if (userData.status === 'success') this.availableUsers = userData.data;

        } catch (e) {
            console.error("Error fetching data for teacher modal:", e);
        }
    },
    async openEditTeacherModal(teacher) {
        await this.fetchSubjectsSafe();
        try {
            this.add_teacher_modal = false;

            // Always refresh dependencies so Edit modal reliably shows latest options.
            const [depRes, subRes] = await Promise.all([
                fetch('/api/admin/departments'),
                fetch('/api/admin/subjects')
            ]);

            if (depRes.ok) {
                const depData = await depRes.json();
                if (depData.status === 'success') {
                    this.departments = Array.isArray(depData.data) ? depData.data : [];
                }
            }

            if (subRes.ok) {
                const subData = await subRes.json();
                if (subData.status === 'success') {
                    this.subjects = Array.isArray(subData.data) ? subData.data : [];
                }
            }

            const teacherDepartmentId = String(teacher?.department_id || '').trim();
            const teacherSubjectId = String(teacher?.subject_id || '').trim();
            const currentSubjectName = String(teacher?.subject_name || teacher?.subject_teach || '').trim().toLowerCase();

            const currentSub = (this.subjects || []).find(s => {
                const subjectId = String(s.id || '').trim();
                const subjectName = String(s.subject_name || '').trim().toLowerCase();
                const sameId = teacherSubjectId && subjectId === teacherSubjectId;
                const sameName = currentSubjectName && subjectName === currentSubjectName;
                const sameDept = !teacherDepartmentId || String(s.department_id || '').trim() === teacherDepartmentId;
                return sameDept && (sameId || sameName);
            });

            this.teacherForm = {
                id: teacher ? teacher.id : '',
                user_id: '',
                teacher_name: teacher ? teacher.teacher_name : '',
                teacher_code: teacher ? teacher.teacher_code : '',
                department_id: teacherDepartmentId,
                subject_id: currentSub ? String(currentSub.id) : ''
            };

            this.edit_teacher_modal = true;
        } catch (e) {
            console.error('Error preparing teacher edit modal:', e);
        }
    },
    async saveTeacher() {
        const selectedSub = this.subjects.find(s => String(s.id) === String(this.teacherForm.subject_id));
        const subjectName = selectedSub ? selectedSub.subject_name : 'មិនទាន់មានមុខវិជ្ជា';

        const payload = {
            user_id: this.teacherForm.user_id,
            teacher_code: this.teacherForm.teacher_code,
            department_id: this.teacherForm.department_id,
            subject_teach: subjectName
        };

        try {
            const res = await fetch('/api/admin/add_teacher', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();
            if (result.status === 'success') {
                this.showToast(result.message, 'success');
                this.add_teacher_modal = false;
                this.fetchTeachers(); // ហៅមកវិញដើម្បីបាត់ N/A
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (e) {
            console.error(e);
        }
    },

    async updateTeacher() {
        const selectedSub = this.subjects.find(s => String(s.id) === String(this.teacherForm.subject_id));
        const subjectName = selectedSub ? selectedSub.subject_name : 'មិនទាន់មានមុខវិជ្ជា';

        const payload = {
            id: this.teacherForm.id,
            teacher_code: this.teacherForm.teacher_code,
            department_id: this.teacherForm.department_id,
            subject_teach: subjectName
        };

        try {
            const res = await fetch('/api/admin/update_teacher', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();
            if (result.status === 'success') {
                this.showToast(result.message, 'success');
                this.edit_teacher_modal = false;
                this.fetchTeachers();
            }
        } catch (e) {
            console.error(e);
        }
    },

    resetTeacherForm() {
        this.teacherForm = { id: '', user_id: '', teacher_name: '', teacher_code: '', department_id: '', subject_id: '' };
    },
    onTeacherDepartmentFilterChange() {
        const dep = String(this.teacherDepartmentFilter || '').trim();
        if (!dep) return;

        const stillValid = (this.subjects || []).some(s =>
            String(s.id) === String(this.teacherSubjectFilter || '') &&
            String(s.department_id || '') === dep
        );

        if (!stillValid) this.teacherSubjectFilter = '';
    },

    get teacherSubjectOptions() {
        const source = Array.isArray(this.subjects) ? this.subjects : [];
        const depMap = new Map(
            (Array.isArray(this.departments) ? this.departments : []).map(d => [String(d.id), d.department_name || ''])
        );
        const selectedDep = String(this.teacherDepartmentFilter || '').trim();

        return source
            .filter(s => !selectedDep || String(s.department_id || '') === selectedDep)
            .map(s => ({
                ...s,
                _department_name: depMap.get(String(s.department_id || '')) || ''
            }))
            .sort((a, b) => {
                const depCmp = String(a._department_name || '').localeCompare(String(b._department_name || ''), undefined, {
                    sensitivity: 'base',
                    numeric: true
                });
                if (depCmp !== 0) return depCmp;

                return String(a.subject_name || '').localeCompare(String(b.subject_name || ''), undefined, {
                    sensitivity: 'base',
                    numeric: true
                });
            });
    },

    get filteredTeachers() {
    let list = Array.isArray(this.teachers) ? [...this.teachers] : [];

    const depFilter = String(this.teacherDepartmentFilter || '').trim();
    const subjId = String(this.teacherSubjectFilter || '').trim();
    const status = String(this.teacherStatusFilter || '').trim();
    const q = String(this.teacherSearchQuery || '').trim().toLowerCase();

    if (depFilter) {
        list = list.filter(t => String(t.department_id || '') === depFilter);
    }

    if (subjId) {
        const subj = (this.subjects || []).find(s => String(s.id) === subjId);
        const subjName = String(subj?.subject_name || '').toLowerCase();

        list = list.filter(t => {
            const tSubjId = String(t.subject_id || '');
            const tSubjText = String(t.subject_teach || t.subject_name || '').toLowerCase();
            return (tSubjId && tSubjId === subjId) || (subjName && tSubjText.includes(subjName));
        });
    }

    if (status) {
        list = list.filter(t => String(t.status || '') === status);
    }

    if (q) {
        list = list.filter(t => {
            const teacherName = String(t.teacher_name || '').toLowerCase();
            const teacherCode = String(t.teacher_code || '').toLowerCase();
            const deptName = String(t.department_name || '').toLowerCase();
            const subjText = String(t.subject_teach || t.subject_name || '').toLowerCase();
            const email = String(t.email || '').toLowerCase();
            const phone = String(t.phone || '').toLowerCase();

            return (
                teacherName.includes(q) ||
                teacherCode.includes(q) ||
                deptName.includes(q) ||
                subjText.includes(q) ||
                email.includes(q) ||
                phone.includes(q)
            );
        });
    }

    return list;
}


    }));
});