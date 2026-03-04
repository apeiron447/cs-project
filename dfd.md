# Data Flow Diagrams — Choice-Based Course Selection System

---

## Level 0: Context Diagram

```mermaid
flowchart TB
    Admin([Admin])
    Student([Student])
    Teacher([Teacher])
    Department([Department])

    System[/"0\nChoice-Based Course\nSelection System"/]

    Admin -->|"Batch config, Course pool,\nSeat matrix, Run allocation,\nLock/Publish, Train AI"| System
    System -->|"Allocation reports,\nTransparency data,\nStatistics, CSV exports"| Admin

    Student -->|"Registration data,\nCourse preferences,\nAcademic history, Interests"| Student
    Student -->|"Preferences,\nAcademic data"| System
    System -->|"Allocation result,\nAI recommendations,\nDashboard data"| Student

    Teacher -->|"Login credentials"| System
    System -->|"Allocated students list,\nCSV roster"| Teacher

    Department -->|"Login credentials"| System
    System -->|"Department students,\nCSV export"| Department
```

---

## Level 1: Overview

```mermaid
flowchart LR
    Admin([Admin]) --> P1[/"1.0\nAuthentication"/]
    Student([Student]) --> P1
    Teacher([Teacher]) --> P1
    Dept([Department]) --> P1

    Admin --> P2[/"2.0\nBatch & Course\nManagement"/]
    Admin --> P3[/"3.0\nStudent\nManagement"/]
    Student --> P4[/"4.0\nPreference\nSubmission"/]
    Admin --> P5[/"5.0\nAllocation\nEngine"/]
    Admin --> P6[/"6.0\nAI Recommendation"/]

    P5 --> P7[/"7.0\nReporting &\nExport"/]
    P7 --> Admin
    P7 --> Student
    P7 --> Teacher
    P7 --> Dept
    P6 --> Student
```

---

## Level 1a: Authentication & Setup (Processes 1.0 – 3.0)

```mermaid
flowchart TB
    Admin([Admin])
    Student([Student])
    Teacher([Teacher])
    Dept([Department])

    P1[/"1.0\nUser\nAuthentication"/]
    P2[/"2.0\nBatch & Course\nManagement"/]
    P3[/"3.0\nStudent\nManagement"/]

    DS1[(D1: Users)]
    DS2[(D2: Departments\n& Programmes)]
    DS3[(D3: Batches)]
    DS4[(D4: Courses &\nSeat Matrix)]
    DS5[(D5: Students &\nAcademic History)]

    Admin -->|"Credentials"| P1
    Student -->|"Credentials"| P1
    Teacher -->|"Credentials"| P1
    Dept -->|"Credentials"| P1
    P1 <-->|"Verify/Fetch user"| DS1

    Admin -->|"Create batch, Add courses\nto pool, Set seat matrix"| P2
    P2 <-->|"Read/Write departments,\nprogrammes"| DS2
    P2 <-->|"Read/Write batches,\ncourse pool"| DS3
    P2 <-->|"Read/Write courses,\nseat matrix"| DS4

    Admin -->|"Register student,\nEnter academic data"| P3
    P3 <-->|"Read/Write student\nrecords"| DS5
    P3 -->|"Lookup batch"| DS3
    P3 -->|"Lookup department"| DS2
```

---

## Level 1b: Preference & Allocation (Processes 4.0 – 5.0)

```mermaid
flowchart TB
    Admin([Admin])
    Student([Student])

    P4[/"4.0\nPreference\nSubmission"/]
    P5[/"5.0\nAllocation\nEngine"/]

    DS3[(D3: Batches)]
    DS4[(D4: Courses &\nSeat Matrix)]
    DS5[(D5: Students &\nAcademic History)]
    DS6[(D6: Preferences)]
    DS7[(D7: Allocations)]

    Student -->|"Submit ranked\ncourse preferences"| P4
    P4 -->|"Validate against\ncourse pool"| DS3
    P4 -->|"Check course\navailability"| DS4
    P4 <-->|"Read/Write\npreferences"| DS6
    P4 -->|"Check lock status"| DS3
    P4 -->|"Verify student\n& department"| DS5

    Admin -->|"Trigger allocation"| P5
    P5 -->|"Fetch students\nsorted by merit"| DS5
    P5 -->|"Read preferences\nin priority order"| DS6
    P5 <-->|"Read/Decrement\nseat matrix"| DS4
    P5 -->|"Write allocation\nresults"| DS7
```

---

## Level 1c: AI Recommendation & Reporting (Processes 6.0 – 7.0)

```mermaid
flowchart TB
    Admin([Admin])
    Student([Student])
    Teacher([Teacher])
    Dept([Department])

    P6[/"6.0\nAI Recommendation\nModule"/]
    P7[/"7.0\nReporting &\nExport"/]

    DS4[(D4: Courses &\nSeat Matrix)]
    DS5[(D5: Students &\nAcademic History)]
    DS6[(D6: Preferences)]
    DS7[(D7: Allocations)]
    DS8[(D8: AI Model)]

    Admin -->|"Train model"| P6
    P6 -->|"Fetch academic\nhistory & interests"| DS5
    P6 -->|"Fetch historical\nallocations"| DS7
    P6 -->|"Fetch course\nmetadata"| DS4
    P6 <-->|"Save/Load\ntrained model"| DS8
    P6 -->|"Suitability scores"| Student

    P7 -->|"Read allocations"| DS7
    P7 -->|"Read students"| DS5
    P7 -->|"Read courses"| DS4
    P7 -->|"Read preferences"| DS6
    P7 -->|"Allocation reports,\nTransparency, CSV"| Admin
    P7 -->|"Allocation status"| Student
    P7 -->|"Student roster"| Teacher
    P7 -->|"Dept students"| Dept
```

---

## Level 2: Allocation Engine (Process 5.0)

```mermaid
flowchart TB
    Admin([Admin])

    P5_1[/"5.1\nFetch & Sort\nStudents by Merit"/]
    P5_2[/"5.2\nIterate\nPreferences"/]
    P5_3[/"5.3\nCheck Seat\nAvailability"/]
    P5_4[/"5.4\nAllocate or\nWaitlist"/]
    P5_5[/"5.5\nCalculate\nTransparency Data"/]

    DS4[(D4: Courses &\nSeat Matrix)]
    DS5[(D5: Students)]
    DS6[(D6: Preferences)]
    DS7[(D7: Allocations)]

    Admin -->|"Trigger allocation\nfor batch"| P5_1
    P5_1 -->|"Read students\nin batch"| DS5
    P5_1 -->|"Sorted student list\n(by qualifying_marks DESC)"| P5_2

    P5_2 -->|"Read student\npreferences"| DS6
    P5_2 -->|"Student + preference\n(in priority order)"| P5_3

    P5_3 -->|"Check category seats\nthen general seats"| DS4
    P5_3 -->|"Seat available:\nAllocate"| P5_4
    P5_3 -->|"No seats in any\npreference: Waitlist"| P5_4

    P5_4 -->|"Decrement\nremaining seats"| DS4
    P5_4 -->|"Write allocation\n(ALLOCATED/WAITLISTED)"| DS7

    P5_4 -->|"Allocation complete"| P5_5
    P5_5 -->|"Read all allocations"| DS7
    P5_5 -->|"Read student marks"| DS5
    P5_5 -->|"Calculate merit ranks,\ncutoffs per category"| DS7
```

---

## Level 2: AI Recommendation Module (Process 6.0)

```mermaid
flowchart TB
    Admin([Admin])
    Student([Student])

    P6_1[/"6.1\nCollect\nTraining Data"/]
    P6_2[/"6.2\nExtract\nFeatures"/]
    P6_3[/"6.3\nTrain ML Model\n(RandomForest)"/]
    P6_4[/"6.4\nScore Courses\nfor Student"/]

    DS4[(D4: Courses)]
    DS5[(D5: Students &\nAcademic History)]
    DS7[(D7: Allocations)]
    DS8[(D8: AI Model)]

    Admin -->|"Trigger training"| P6_1
    P6_1 -->|"Fetch historical\nallocations"| DS7
    P6_1 -->|"Fetch student\nprofiles"| DS5
    P6_1 -->|"Fetch course\nmetadata"| DS4
    P6_1 -->|"Training samples"| P6_2

    P6_2 -->|"Extract: CGPA, avg_marks,\ntag_overlap, difficulty,\ncredits"| P6_3
    P6_3 -->|"Save trained\nmodel"| DS8

    Student -->|"Request\nrecommendations"| P6_4
    P6_4 -->|"Load model"| DS8
    P6_4 -->|"Fetch student\nacademic data"| DS5
    P6_4 -->|"Fetch available\ncourses"| DS4
    P6_4 -->|"Suitability scores:\nHighly Recommended (75+)\nGood Fit (50-74)\nChallenging (<50)"| Student
```

---

## Data Store Descriptions

| Store | Contents | Source Tables |
|-------|----------|---------------|
| D1: Users | Login credentials, roles (Admin/Student/Teacher/Department) | `user` |
| D2: Departments & Programmes | 20 departments, 40+ programmes, academic structure | `department`, `programme` |
| D3: Batches | Student cohorts, semester info, lock/publish flags, course pool | `batch`, `course_pool` |
| D4: Courses & Seat Matrix | Course offerings, category-wise seat allocation | `course`, `seat_matrix` |
| D5: Students & Academic History | Student profiles, marks, CGPA, interests | `student`, `student_academic_history`, `student_subject_mark`, `student_interest` |
| D6: Preferences | Ranked course preferences per student | `preference` |
| D7: Allocations | Final allocation results with status | `allocation` |
| D8: AI Model | Trained RandomForestRegressor model file | `ai_model/` directory |
