// ---------------------------------------------------------------
// WarehouseService: talks to /api/warehouses (backend/app/api/warehouse.py).
// Photos go straight from the browser to S3 with a short-lived link.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Same shapes as the backend's warehouse schemas.
export interface Photo {
  id: string;
  status: 'PENDING' | 'UPLOADED';
  view_url: string | null;
}

export interface Warehouse {
  id: string;
  name: string;
  address: string;
  city_id: string;
  city_name: string | null;
  pincode: string;
  capacity: number;
  unit_id: string;
  unit_name: string | null;
  storage_type_id: string;
  storage_type_name: string | null;
  stock_type_ids: string[];
  price_per_unit_month: string; // Decimal comes back as text
  status: 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED';
  photos: Photo[];
  missing: string[]; // what still blocks "submit" (empty = ready)
  review_note: string | null; // why an admin sent it back (M6)
  owner_name?: string | null; // admin screens only
  owner_email?: string | null;
}

export interface WarehouseInput {
  name: string;
  address: string;
  city_id: string;
  pincode: string;
  capacity: number;
  unit_id: string;
  storage_type_id: string;
  stock_type_ids: string[];
  price_per_unit_month: string;
}

export interface PhotoUpload {
  photo_id: string;
  upload_url: string;
  content_type: string;
}

const BASE = '/api/warehouses';

@Injectable({ providedIn: 'root' })
export class WarehouseService {
  private readonly http = inject(HttpClient);

  list(): Observable<Warehouse[]> {
    return this.http.get<Warehouse[]>(BASE);
  }

  get(id: string): Observable<Warehouse> {
    return this.http.get<Warehouse>(`${BASE}/${id}`);
  }

  create(body: WarehouseInput): Observable<Warehouse> {
    return this.http.post<Warehouse>(BASE, body);
  }

  update(id: string, body: WarehouseInput): Observable<Warehouse> {
    return this.http.put<Warehouse>(`${BASE}/${id}`, body);
  }

  submit(id: string): Observable<Warehouse> {
    return this.http.post<Warehouse>(`${BASE}/${id}/submit`, {});
  }

  /** Step 1 of a photo: ask for a link to upload one photo to. */
  requestPhoto(id: string, contentType: string): Observable<PhotoUpload> {
    return this.http.post<PhotoUpload>(`${BASE}/${id}/photos`, { content_type: contentType });
  }

  /** Step 2: send the file itself to S3 (not to our API). */
  uploadFile(uploadUrl: string, file: File): Observable<unknown> {
    return this.http.put(uploadUrl, file, { headers: { 'Content-Type': file.type } });
  }

  /** Step 3: tell the API the upload finished, so it checks the file. */
  confirmPhoto(id: string, photoId: string): Observable<Warehouse> {
    return this.http.post<Warehouse>(`${BASE}/${id}/photos/${photoId}/confirm`, {});
  }

  deletePhoto(id: string, photoId: string): Observable<Warehouse> {
    return this.http.delete<Warehouse>(`${BASE}/${id}/photos/${photoId}`);
  }
}
