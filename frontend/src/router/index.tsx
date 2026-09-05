import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { IntakePage } from '../pages/IntakePage';
import { HealthPage } from '../pages/HealthPage';
import { DocumentsPage } from '../pages/DocumentsPage';
import { ConflictsPage } from '../pages/ConflictsPage';
import { TimelinePage } from '../pages/TimelinePage';
import { MedicalRecordPage } from '../pages/MedicalRecordPage';
import { VerificationPage } from '../pages/VerificationPage';
import { NotFoundPage } from '../pages/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'record',
        element: <MedicalRecordPage />,
      },
      {
        path: 'records',
        element: <MedicalRecordPage />,
      },
      {
        path: 'verification',
        element: <VerificationPage />,
      },

      {
        path: 'intake',
        element: <IntakePage />,
      },
      {
        path: 'health',
        element: <HealthPage />,
      },
      {
        path: 'documents',
        element: <DocumentsPage />,
      },
      {
        path: 'conflicts',
        element: <ConflictsPage />,
      },
      {
        path: 'timeline',
        element: <TimelinePage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

