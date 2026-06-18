# EduCore API Reference (`/api/v1`)

All endpoints are JSON. Authenticated routes require `Authorization: Bearer <access_token>`.
Set `Accept-Language: uz|en` for localized error messages. Bot routes require `X-Bot-Token`.

## auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Me |
| POST | `/api/v1/auth/refresh` | Refresh |
| POST | `/api/v1/auth/register` | Register |

## me

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/me/attendance` | My Attendance |
| GET | `/api/v1/me/groups` | My Groups |
| GET | `/api/v1/me/lessons` | My Lessons |
| GET | `/api/v1/me/payments` | My Payments |

## students

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/students` | List Students |
| POST | `/api/v1/students` | Create Student |
| DELETE | `/api/v1/students/{student_id}` | Delete Student |
| GET | `/api/v1/students/{student_id}` | Get Student |
| PATCH | `/api/v1/students/{student_id}` | Update Student |
| GET | `/api/v1/students/{student_id}/attendance` | Student Attendance |
| GET | `/api/v1/students/{student_id}/payments` | Student Payments |

## teachers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/teachers` | List Teachers |
| POST | `/api/v1/teachers` | Create Teacher |
| DELETE | `/api/v1/teachers/{teacher_id}` | Delete Teacher |
| GET | `/api/v1/teachers/{teacher_id}` | Get Teacher |
| PATCH | `/api/v1/teachers/{teacher_id}` | Update Teacher |

## groups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/groups` | List Groups |
| POST | `/api/v1/groups` | Create Group |
| DELETE | `/api/v1/groups/{group_id}` | Delete Group |
| GET | `/api/v1/groups/{group_id}` | Get Group |
| PATCH | `/api/v1/groups/{group_id}` | Update Group |
| GET | `/api/v1/groups/{group_id}/students` | Group Students |
| POST | `/api/v1/groups/{group_id}/students` | Assign Students |
| DELETE | `/api/v1/groups/{group_id}/students/{student_id}` | Remove Student |

## courses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/courses` | List Courses |
| POST | `/api/v1/courses` | Create Course |
| POST | `/api/v1/courses/lessons` | Create Lesson |
| DELETE | `/api/v1/courses/lessons/{lesson_id}` | Delete Lesson |
| PATCH | `/api/v1/courses/lessons/{lesson_id}` | Update Lesson |
| POST | `/api/v1/courses/lessons/{lesson_id}/progress` | Mark Progress |
| DELETE | `/api/v1/courses/{course_id}` | Delete Course |
| PATCH | `/api/v1/courses/{course_id}` | Update Course |
| GET | `/api/v1/courses/{course_id}/lessons` | List Lessons |

## attendance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/attendance` | Mark Attendance |
| GET | `/api/v1/attendance/group/{group_id}` | Group Attendance |

## payments

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/payments` | List Payments |
| POST | `/api/v1/payments` | Create Payment |
| PATCH | `/api/v1/payments/{payment_id}` | Update Payment |

## dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard/stats` | Dashboard Stats |

## bot

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/bot/language` | Set Language |
| POST | `/api/v1/bot/link` | Link Account |
| GET | `/api/v1/bot/me` | Bot Me |
| GET | `/api/v1/bot/parent/child/{student_id}/attendance` | Parent Child Attendance |
| GET | `/api/v1/bot/parent/child/{student_id}/payments` | Parent Child Payments |
| GET | `/api/v1/bot/parent/children` | Parent Children |
| GET | `/api/v1/bot/student/attendance` | Student Attendance |
| GET | `/api/v1/bot/student/groups` | Student Groups |
| GET | `/api/v1/bot/student/lessons` | Student Lessons |
| GET | `/api/v1/bot/student/payments` | Student Payments |
| POST | `/api/v1/bot/teacher/attendance` | Teacher Mark Attendance |
| GET | `/api/v1/bot/teacher/group/{group_id}/students` | Teacher Group Students |
| GET | `/api/v1/bot/teacher/groups` | Teacher Groups |

## health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health |
