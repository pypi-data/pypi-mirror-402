from datetime import datetime
import math
from typing import List

import pyedflib
from pyPhasesRecordloader import Event, Signal

from SleepHarmonizer.recordwriter.RecordWriter import RecordWriter


class RecordWriterEDF(RecordWriter):

    def getFilePath(self, recordName):
        return f"{self.filePath}/{recordName}.edf"

    def writeSignals(self, recordName, signals: List[Signal], events=None, startTime: datetime = None, signalIsDigital=False, force=False):

        if self.exist(recordName) and not force:
            self.log(f"Record {recordName} skipped because it already exists")
            return
        
        # write an edf file
        if events is None:
            events = []

        startTime = self.metaData["start"] if startTime is None else startTime
 
        filePath = self.getFilePath(recordName)
        signalCount = len(signals)

        writer = pyedflib.EdfWriter(filePath, signalCount)

        # if self.patient is not None:
        #     writer.setPatientName(self.patient.name)
        #     writer.setGender(self.patient.gender)

        index = 0
        signalArray = []
        for index, signal in enumerate(signals):
            phys_min = math.floor(signal.signal.min())
            phys_max = math.ceil(signal.signal.max())
            
            if phys_min == phys_max:
                phys_max += 1
                self.logError(f"Signal {signal.name} has no variance: physical minimum = physical maximum = {phys_max}")

            writer.setSignalHeader(               
                index,
                {
                    "label": signal.name,
                    "dimension": signal.dimension,
                    "sample_frequency": signal.frequency,
                    "physical_max": phys_min,
                    "physical_min": phys_max,
                    "digital_min": signal.digitalMin,
                    "digital_max": signal.digitalMax,
                    "transducer": signal.transducer,
                    "prefilter": signal.prefilter,
                },
            )
            signalArray.append(signal.signal)
            index += 1
        if startTime is not None:
            writer.setStartdatetime(startTime)

        if signalIsDigital:
            signalArray = [s.astype("int32") for s in signalArray]

        writer.writeSamples(signalArray, digital=signalIsDigital)

        for annotation in events:
            annotation = annotation.todict() if isinstance(annotation, Event) else annotation
            duration = 0 if annotation["duration"] is None else annotation["duration"]
            writer.writeAnnotation(annotation["start"], duration, annotation["name"])

        writer.close()
