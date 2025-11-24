import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  HomeIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  CurrencyDollarIcon,
  PlusIcon,
  UserCircleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const Layout = ({ children }) => {
  const { user, logout, isStaff, canApprove, isFinance } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Navigation items based on user role
  const getNavigationItems = () => {
    const items = [
      {
        name: 'Dashboard',
        href: '/dashboard',
        icon: HomeIcon,
        current: location.pathname === '/dashboard' || location.pathname === '/',
      },
    ];

    if (isStaff()) {
      items.push(
        {
          name: 'My Requests',
          href: '/dashboard',
          icon: DocumentTextIcon,
          current: location.pathname === '/dashboard',
        },
        {
          name: 'New Request',
          href: '/requests/new',
          icon: PlusIcon,
          current: location.pathname === '/requests/new',
        }
      );
    }

    if (canApprove()) {
      items.push({
        name: 'Pending Approvals',
        href: '/dashboard',
        icon: CheckCircleIcon,
        current: location.pathname === '/dashboard',
      });
    }

    if (isFinance()) {
      items.push({
        name: 'Approved Requests',
        href: '/dashboard',
        icon: CurrencyDollarIcon,
        current: location.pathname === '/dashboard',
      });
    }

    return items;
  };

  const navigation = getNavigationItems();

  const getRoleDisplayName = () => {
    switch (user?.role) {
      case 'staff':
        return 'Staff';
      case 'approver_lvl1':
        return 'Approver Level 1';
      case 'approver_lvl2':
        return 'Approver Level 2';
      case 'finance':
        return 'Finance';
      default:
        return 'User';
    }
  };

  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 flex z-40 md:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)}></div>
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" />
            </button>
          </div>
          <SidebarContent navigation={navigation} user={user} getRoleDisplayName={getRoleDisplayName} onLogout={handleLogout} />
        </div>
        <div className="flex-shrink-0 w-14"></div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <SidebarContent navigation={navigation} user={user} getRoleDisplayName={getRoleDisplayName} onLogout={handleLogout} />
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Top bar */}
        <div className="md:hidden pl-1 pt-1 sm:pl-3 sm:pt-3 bg-white shadow">
          <button
            className="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>

        {/* Page content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

const SidebarContent = ({ navigation, user, getRoleDisplayName, onLogout }) => {
  return (
    <div className="flex flex-col h-0 flex-1 bg-white shadow-lg">
      {/* Logo */}
      <div className="flex items-center h-16 flex-shrink-0 px-4 bg-blue-600">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-8 w-8 bg-white rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-bold text-sm">P2P</span>
          </div>
          <span className="ml-2 text-white font-medium">Procure-to-Pay</span>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`${
                  item.current
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                } group flex items-center pl-2 py-2 text-sm font-medium border-l-4 transition-colors duration-150`}
              >
                <Icon
                  className={`${
                    item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                  } mr-3 flex-shrink-0 h-6 w-6`}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User info */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
              <p className="text-xs text-gray-500">{getRoleDisplayName()}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="mt-2 w-full text-left text-sm text-gray-500 hover:text-gray-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
};

export default Layout;