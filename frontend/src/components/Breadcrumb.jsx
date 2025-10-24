// frontend/src/components/Breadcrumb.jsx

import { Link } from 'react-router-dom';

export default function Breadcrumb({ items, customerCode }) {
  return (
    <div className="mb-6 flex items-center space-x-2 text-sm text-oxford-600 font-medium">
      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-2">
          {index > 0 && <span className="text-oxford-400">/</span>}
          {item.link ? (
            <Link to={item.link} className="hover:text-oxford-800 transition">
              {item.label}
            </Link>
          ) : (
            <span className="text-oxford-900 font-semibold">{item.label}</span>
          )}
        </div>
      ))}
      {customerCode && (
        <span className="ml-4 px-3 py-1 bg-encora-yellow-400 text-oxford-900 rounded-lg text-xs font-bold">
          Customer: {customerCode}
        </span>
      )}
    </div>
  );
}