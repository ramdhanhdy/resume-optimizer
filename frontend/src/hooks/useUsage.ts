import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface UsageInfo {
  remaining: number;
  total: number;
  used: number;
  isSubscribed: boolean;
  loading: boolean;
  error: string | null;
}

export function useUsage(): UsageInfo & { refetch: () => void } {
  const { user } = useAuth();
  const [usage, setUsage] = useState<UsageInfo>({
    remaining: 5,
    total: 5,
    used: 0,
    isSubscribed: false,
    loading: true,
    error: null,
  });

  const fetchUsage = async () => {
    if (!user) {
      setUsage(prev => ({ ...prev, loading: false }));
      return;
    }

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const response = await fetch(`${API_BASE_URL}/api/usage`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setUsage({
          remaining: data.remaining,
          total: data.cap,
          used: data.used,
          isSubscribed: data.is_subscribed,
          loading: false,
          error: null,
        });
      } else {
        setUsage(prev => ({ 
          ...prev, 
          loading: false, 
          error: 'Failed to fetch usage' 
        }));
      }
    } catch (error) {
      console.error('Failed to fetch usage:', error);
      setUsage(prev => ({ 
        ...prev, 
        loading: false, 
        error: 'Failed to fetch usage' 
      }));
    }
  };

  useEffect(() => {
    fetchUsage();
  }, [user]);

  return { ...usage, refetch: fetchUsage };
}
